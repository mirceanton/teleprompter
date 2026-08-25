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
	mu           sync.Mutex
	participants map[string]*Participant
	script       string
	hasScript    bool                              // whether SetScript has ever been called, vs. script being legitimately ""
	settings     map[string]map[string]interface{} // participant ID -> last known settings
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

// SetScriptFromController stores text as the hub's persisted script only if
// participantID currently holds the controller role. "text" messages are
// only ever sent by the controller today, but this guards the durable
// server-side state explicitly rather than trusting the sender.
func (h *Hub) SetScriptFromController(participantID, text string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if p, ok := h.participants[participantID]; !ok || p.Role != "controller" {
		return
	}
	h.script = text
	h.hasScript = true
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
			if role == "controller" {
				h.SendState(p.ID)
			}
			continue
		}

		if msgType == "text" {
			if content, ok := msg["content"].(string); ok {
				h.SetScriptFromController(p.ID, content)
			}
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
