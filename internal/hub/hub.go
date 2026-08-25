package hub

import (
	"crypto/rand"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	writeWait      = 10 * time.Second
	pongWait       = 60 * time.Second
	pingPeriod     = (pongWait * 9) / 10
	maxMessageSize = 512 * 1024
)

type Participant struct {
	ID       string    `json:"id"`
	Role     string    `json:"role"`
	JoinedAt time.Time `json:"joined_at"`
	conn     *websocket.Conn
	Send     chan []byte
}

type Hub struct {
	mu              sync.Mutex
	participants    map[string]*Participant
	script          string
	hasScript       bool                              // whether SetScript has ever been called, vs. script being legitimately ""
	settings        map[string]map[string]interface{} // participant ID -> last known settings
	markdownEnabled bool                              // last known state of the controller's markdown toggle
	isPlaying       bool                              // last known play/pause state
	atEnd           bool                              // whether the last known position command was go_to_end rather than go_to_beginning
}

func New() *Hub {
	return &Hub{
		participants: make(map[string]*Participant),
		settings:     make(map[string]map[string]interface{}),
	}
}

func newID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}

func (h *Hub) Register(conn *websocket.Conn) *Participant {
	p := &Participant{
		ID:       newID(),
		JoinedAt: time.Now(),
		conn:     conn,
		Send:     make(chan []byte, 256),
	}

	welcome, _ := json.Marshal(map[string]interface{}{
		"type":           "welcome",
		"participant_id": p.ID,
	})

	h.mu.Lock()
	h.participants[p.ID] = p
	connUpdate, _ := json.Marshal(map[string]interface{}{
		"type":             "connection_update",
		"connection_count": len(h.participants),
		"participants":     h.participantListLocked(),
	})
	p.Send <- welcome
	for id, other := range h.participants {
		if id == p.ID {
			continue
		}
		select {
		case other.Send <- connUpdate:
		default:
		}
	}
	h.mu.Unlock()

	return p
}

func (h *Hub) Unregister(p *Participant) {
	h.mu.Lock()
	if _, ok := h.participants[p.ID]; !ok {
		h.mu.Unlock()
		return
	}
	delete(h.participants, p.ID)
	delete(h.settings, p.ID)
	close(p.Send)
	leftMsg, _ := json.Marshal(map[string]interface{}{
		"type":             "participant_left",
		"participant_id":   p.ID,
		"connection_count": len(h.participants),
		"participants":     h.participantListLocked(),
	})
	for _, other := range h.participants {
		select {
		case other.Send <- leftMsg:
		default:
		}
	}
	h.mu.Unlock()
}

func (h *Hub) Broadcast(data []byte, excludeID string) {
	h.mu.Lock()
	for id, p := range h.participants {
		if id == excludeID {
			continue
		}
		select {
		case p.Send <- data:
		default:
		}
	}
	h.mu.Unlock()
}

func (h *Hub) Unicast(targetID string, data []byte) {
	h.mu.Lock()
	p, ok := h.participants[targetID]
	h.mu.Unlock()
	if ok {
		select {
		case p.Send <- data:
		default:
		}
	}
}

func (h *Hub) UpdateRole(participantID, role string) {
	h.mu.Lock()
	if p, ok := h.participants[participantID]; ok {
		p.Role = role
	}
	update, _ := json.Marshal(map[string]interface{}{
		"type":         "participants_update",
		"participants": h.participantListLocked(),
	})
	for _, p := range h.participants {
		select {
		case p.Send <- update:
		default:
		}
	}
	h.mu.Unlock()
}

func (h *Hub) ConnectionCount() int {
	h.mu.Lock()
	defer h.mu.Unlock()
	return len(h.participants)
}

// SetScript stores the latest script text so a controller that (re)connects
// can rehydrate it instead of falling back to its hardcoded default.
func (h *Hub) SetScript(text string) {
	h.mu.Lock()
	h.script = text
	h.hasScript = true
	h.mu.Unlock()
}

// isControllerLocked reports whether participantID currently holds the
// controller role. h.mu must already be held by the caller.
func (h *Hub) isControllerLocked(participantID string) bool {
	p, ok := h.participants[participantID]
	return ok && p.Role == "controller"
}

// SetScriptFromController stores text as the hub's persisted script only if
// participantID currently holds the controller role. "text" messages are
// only ever sent by the controller today, but this guards the durable
// server-side state explicitly rather than trusting the sender.
//
// A new script also resets playback on every teleprompter client-side (see
// the "text" case in teleprompter.html's handleMessage, which always calls
// resetScrolling()), so the hub's retained playback/position state is reset
// to match.
func (h *Hub) SetScriptFromController(participantID, text string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if !h.isControllerLocked(participantID) {
		return
	}
	h.script = text
	h.hasScript = true
	h.isPlaying = false
	h.atEnd = false
}

// SetMarkdownFromController records the last-known state of the controller's
// markdown-rendering toggle, gated to the controller role like
// SetScriptFromController.
func (h *Hub) SetMarkdownFromController(participantID string, enabled bool) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if !h.isControllerLocked(participantID) {
		return
	}
	h.markdownEnabled = enabled
}

// SetPlaybackFromController records the hub's last-known play/pause and
// beginning/end position state in response to a controller-originated
// playback message (msgType is one of "start", "pause", "go_to_beginning",
// or "go_to_end"), gated to the controller role like SetScriptFromController.
//
// Note this only tracks the coarse beginning/end position, not fine-grained
// "scroll_lines" nudges: those are relative moves interpreted client-side
// using each teleprompter's own font size, so there is no single absolute
// position the hub could faithfully replay to a newly-connecting device.
func (h *Hub) SetPlaybackFromController(participantID, msgType string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if !h.isControllerLocked(participantID) {
		return
	}
	switch msgType {
	case "start":
		h.isPlaying = true
		h.atEnd = false
	case "pause":
		h.isPlaying = false
	case "go_to_beginning":
		h.isPlaying = false
		h.atEnd = false
	case "go_to_end":
		h.isPlaying = false
		h.atEnd = true
	}
}

// settingsFields maps a per-prompter settings message type to the field it
// carries and the key that field is recorded under, matching the shape the
// controller already keeps client-side in state.prompterSettings.
var settingsFields = map[string]struct {
	msgKey  string
	snapKey string
}{
	"speed":          {"value", "scrollSpeed"},
	"width":          {"value", "textWidth"},
	"font_size":      {"value", "fontSize"},
	"lines_per_step": {"value", "linesPerStep"},
	"mirror":         {"horizontal", "horizontalMirror"},
}

// RecordSetting remembers the latest value of a per-prompter setting for
// targetID, if msgType is a known settings message. It is a no-op for any
// other message type, and for a target that isn't currently connected.
func (h *Hub) RecordSetting(targetID, msgType string, msg map[string]interface{}) {
	field, ok := settingsFields[msgType]
	if !ok {
		return
	}
	value, ok := msg[field.msgKey]
	if !ok {
		return
	}

	h.mu.Lock()
	defer h.mu.Unlock()
	if _, ok := h.participants[targetID]; !ok {
		return
	}
	snap, ok := h.settings[targetID]
	if !ok {
		snap = make(map[string]interface{})
		h.settings[targetID] = snap
	}
	snap[field.snapKey] = value
}

// SendState unicasts the hub's persisted script and per-prompter settings to
// participantID. Called when a controller identifies itself, so a
// reconnecting or brand-new controller tab can rehydrate the last known
// state instead of starting from its hardcoded default script.
func (h *Hub) SendState(participantID string) {
	h.mu.Lock()
	// Every entry in h.settings belongs to a currently-connected participant:
	// Unregister deletes it under this same lock when a participant leaves.
	settings := make(map[string]interface{}, len(h.settings))
	for id, snap := range h.settings {
		cp := make(map[string]interface{}, len(snap))
		for k, v := range snap {
			cp[k] = v
		}
		settings[id] = cp
	}
	data, _ := json.Marshal(map[string]interface{}{
		"type":       "state_sync",
		"script":     h.script,
		"has_script": h.hasScript,
		"settings":   settings,
	})
	h.mu.Unlock()

	h.Unicast(participantID, data)
}

// SendTeleprompterState unicasts the hub's persisted script, markdown
// toggle, and playback/position state to participantID, along with
// participantID's own settings snapshot (if any was previously recorded for
// its ID). Called when a teleprompter identifies itself, so a reconnecting
// or brand-new teleprompter tab can rehydrate the last known state instead
// of sitting on a blank screen until a controller notices the new
// connection and pushes a manual resync.
//
// Unlike SendState, which gives a controller every participant's settings
// keyed by ID, a teleprompter only needs its own settings.
//
// In practice the own-settings snapshot is always empty today: h.settings[ID]
// is only populated once a controller addresses this participant's ID in a
// target_id'd message, which requires the controller to already know that
// ID — but IDs are freshly assigned on every connect (see newID/Register) and
// aren't stable across reconnects (Unregister deletes the entry), so no
// controller can have addressed this ID before this very "mode: teleprompter"
// identification fires. This field is kept for architectural symmetry with
// SendState's controller path and will become useful once/if the app gains
// stable per-device identity across reconnects; it is inert until then.
func (h *Hub) SendTeleprompterState(participantID string) {
	h.mu.Lock()
	settings := make(map[string]interface{})
	if snap, ok := h.settings[participantID]; ok {
		for k, v := range snap {
			settings[k] = v
		}
	}
	data, _ := json.Marshal(map[string]interface{}{
		"type":             "state_sync",
		"script":           h.script,
		"has_script":       h.hasScript,
		"markdown_enabled": h.markdownEnabled,
		"is_playing":       h.isPlaying,
		"at_end":           h.atEnd,
		"settings":         settings,
	})
	h.mu.Unlock()

	h.Unicast(participantID, data)
}

func (h *Hub) participantListLocked() []map[string]interface{} {
	result := make([]map[string]interface{}, 0, len(h.participants))
	for _, p := range h.participants {
		result = append(result, map[string]interface{}{
			"id":        p.ID,
			"role":      p.Role,
			"joined_at": p.JoinedAt,
		})
	}
	return result
}

func (p *Participant) ReadPump(h *Hub) {
	defer func() {
		h.Unregister(p)
		p.conn.Close()
	}()

	p.conn.SetReadLimit(maxMessageSize)
	_ = p.conn.SetReadDeadline(time.Now().Add(pongWait))
	p.conn.SetPongHandler(func(string) error {
		return p.conn.SetReadDeadline(time.Now().Add(pongWait))
	})

	for {
		_, raw, err := p.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("ws read error: %v", err)
			}
			return
		}

		var msg map[string]interface{}
		if err := json.Unmarshal(raw, &msg); err != nil {
			continue
		}

		msgType, _ := msg["type"].(string)
		if msgType == "mode" {
			role, _ := msg["mode"].(string)
			h.UpdateRole(p.ID, role)
			switch role {
			case "controller":
				h.SendState(p.ID)
			case "teleprompter":
				h.SendTeleprompterState(p.ID)
			}
			continue
		}

		// Note: the SetXFromController calls below only gate the hub's
		// *persisted* replay state to the controller role; the raw message is
		// still broadcast to all clients below regardless of sender role, so
		// a non-controller sender can make live clients diverge from what
		// the hub reports on the next state_sync. This mirrors an
		// already-accepted tradeoff for "text" from the prior PR; closing it
		// for all of these is out of scope here.
		switch msgType {
		case "text":
			if content, ok := msg["content"].(string); ok {
				h.SetScriptFromController(p.ID, content)
			}
		case "markdown":
			if enabled, ok := msg["enabled"].(bool); ok {
				h.SetMarkdownFromController(p.ID, enabled)
			}
		case "start", "pause", "go_to_beginning", "go_to_end":
			h.SetPlaybackFromController(p.ID, msgType)
		}

		if targetID, ok := msg["target_id"].(string); ok && targetID != "" {
			h.RecordSetting(targetID, msgType, msg)
			delete(msg, "target_id")
			fwd, _ := json.Marshal(msg)
			h.Unicast(targetID, fwd)
		} else {
			h.Broadcast(raw, p.ID)
		}
	}
}

func (p *Participant) WritePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		p.conn.Close()
	}()

	for {
		select {
		case msg, ok := <-p.Send:
			_ = p.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				_ = p.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			if err := p.conn.WriteMessage(websocket.TextMessage, msg); err != nil {
				return
			}
		case <-ticker.C:
			_ = p.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := p.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}
