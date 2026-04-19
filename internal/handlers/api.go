package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
	"github.com/gorilla/websocket"
	"github.com/mirceanton/teleprompter/internal/hub"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin:     func(r *http.Request) bool { return true },
}

func WebSocketHandler(h *hub.Hub) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			return
		}
		p := h.Register(conn)
		go p.WritePump()
		p.ReadPump(h)
	}
}

func HealthHandler(h *hub.Hub) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"status":           "ok",
			"connection_count": h.ConnectionCount(),
		})
	}
}

func LiveHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
}

func PlaybackBroadcast(h *hub.Hub, msg string) http.HandlerFunc {
	data := []byte(msg)
	return func(w http.ResponseWriter, r *http.Request) {
		h.Broadcast(data, "")
		w.WriteHeader(http.StatusNoContent)
	}
}

func ScrollLines(h *hub.Hub, direction string, lines int) http.HandlerFunc {
	data, _ := json.Marshal(map[string]interface{}{
		"type":      "scroll_lines",
		"direction": direction,
		"lines":     lines,
		"smooth":    true,
	})
	return func(w http.ResponseWriter, r *http.Request) {
		h.Broadcast(data, "")
		w.WriteHeader(http.StatusNoContent)
	}
}

func ScrollLinesParam(h *hub.Hub, direction string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lines, err := strconv.Atoi(chi.URLParam(r, "lines"))
		if err != nil || lines < 1 {
			lines = 5
		}
		data, _ := json.Marshal(map[string]interface{}{
			"type":      "scroll_lines",
			"direction": direction,
			"lines":     lines,
			"smooth":    true,
		})
		h.Broadcast(data, "")
		w.WriteHeader(http.StatusNoContent)
	}
}
