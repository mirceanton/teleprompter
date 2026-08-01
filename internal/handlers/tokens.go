package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/mirceanton/teleprompter/internal/auth"
	"github.com/mirceanton/teleprompter/internal/tokens"
)

// TokensListHandler returns the current user's Personal Access Tokens
// (metadata only — the secret is never stored, so it can't be shown again).
func TokensListHandler(store *tokens.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		user, ok := auth.UserFrom(r.Context())
		if !ok {
			http.Error(w, "authentication required", http.StatusUnauthorized)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"tokens": store.List(user.Sub),
		})
	}
}

// TokenCreateHandler mints a new token for the current user and returns the
// raw secret once, alongside its metadata.
func TokenCreateHandler(store *tokens.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		user, ok := auth.UserFrom(r.Context())
		if !ok {
			http.Error(w, "authentication required", http.StatusUnauthorized)
			return
		}
		var body struct {
			Name string `json:"name"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, "invalid JSON body", http.StatusBadRequest)
			return
		}
		name := strings.TrimSpace(body.Name)
		if name == "" {
			http.Error(w, "a token name is required", http.StatusBadRequest)
			return
		}

		raw, meta, err := store.Create(user, name)
		if err != nil {
			http.Error(w, "failed to create token", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"token":        raw,
			"id":           meta.ID,
			"name":         meta.Name,
			"created_at":   meta.CreatedAt,
			"last_used_at": meta.LastUsedAt,
		})
	}
}

// TokenRevokeHandler deletes a token owned by the current user.
func TokenRevokeHandler(store *tokens.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		user, ok := auth.UserFrom(r.Context())
		if !ok {
			http.Error(w, "authentication required", http.StatusUnauthorized)
			return
		}
		id := strings.TrimSpace(r.URL.Query().Get("id"))
		if id == "" {
			http.Error(w, "id query parameter is required", http.StatusBadRequest)
			return
		}
		removed, err := store.Revoke(user.Sub, id)
		if err != nil {
			http.Error(w, "failed to revoke token", http.StatusInternalServerError)
			return
		}
		if !removed {
			http.Error(w, "token not found", http.StatusNotFound)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	}
}
