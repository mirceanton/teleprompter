package handlers

import (
	"context"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/mirceanton/teleprompter/internal/auth"
	"github.com/mirceanton/teleprompter/internal/hub"
	"github.com/mirceanton/teleprompter/internal/session"
)

type ctxKey int

const (
	hubCtxKey ctxKey = iota
	sessionCtxKey
)

// WithHub injects a fixed hub into every request. Used in single-user mode,
// where one global hub serves all connections.
func WithHub(h *hub.Hub) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), hubCtxKey, h)))
		})
	}
}

// SessionAccess resolves the {sessionID} route parameter and enforces access:
// anything but an existing session the current user was granted access to is
// answered with 404, so outsiders cannot distinguish "exists" from "denied".
func SessionAccess(m *session.Manager) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			user, userOK := auth.UserFrom(r.Context())
			sess, sessOK := m.Get(chi.URLParam(r, "sessionID"))
			if !userOK || !sessOK || !sess.CanAccess(user) {
				http.NotFound(w, r)
				return
			}
			ctx := context.WithValue(r.Context(), sessionCtxKey, sess)
			ctx = context.WithValue(ctx, hubCtxKey, sess.Hub)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func hubFrom(r *http.Request) *hub.Hub {
	h, _ := r.Context().Value(hubCtxKey).(*hub.Hub)
	return h
}

func sessionFrom(r *http.Request) *session.Session {
	s, _ := r.Context().Value(sessionCtxKey).(*session.Session)
	return s
}
