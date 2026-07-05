package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin:     func(r *http.Request) bool { return true },
}

// ConnectionCounter reports how many WebSocket connections are live. Both a
// single hub and the multi-user session manager implement it.
type ConnectionCounter interface {
	ConnectionCount() int
}

func WebSocketHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		h := hubFrom(r)
		if h == nil {
			http.NotFound(w, r)
			return
		}
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			return
		}
		p := h.Register(conn)
		go p.WritePump()
		p.ReadPump(h)
	}
}

func HealthHandler(c ConnectionCounter) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"status":           "ok",
			"connection_count": c.ConnectionCount(),
		})
	}
}

func LiveHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
}

func PlaybackBroadcast(msg string) http.HandlerFunc {
	data := []byte(msg)
	return func(w http.ResponseWriter, r *http.Request) {
		if h := hubFrom(r); h != nil {
			h.Broadcast(data, "")
		}
		w.WriteHeader(http.StatusNoContent)
	}
}

func ScrollLines(direction string, lines int) http.HandlerFunc {
	data, _ := json.Marshal(map[string]interface{}{
		"type":      "scroll_lines",
		"direction": direction,
		"lines":     lines,
		"smooth":    true,
	})
	return func(w http.ResponseWriter, r *http.Request) {
		if h := hubFrom(r); h != nil {
			h.Broadcast(data, "")
		}
		w.WriteHeader(http.StatusNoContent)
	}
}

func ScrollLinesParam(direction string) http.HandlerFunc {
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
		if h := hubFrom(r); h != nil {
			h.Broadcast(data, "")
		}
		w.WriteHeader(http.StatusNoContent)
	}
}
