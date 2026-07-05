package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/mirceanton/teleprompter/internal/auth"
	"github.com/mirceanton/teleprompter/internal/session"
)

// requireOwner returns the session when the current user owns it, or writes
// a 403 and returns nil. Only owners may inspect or change membership.
func requireOwner(w http.ResponseWriter, r *http.Request) *session.Session {
	sess := sessionFrom(r)
	user, ok := auth.UserFrom(r.Context())
	if sess == nil || !ok || !sess.IsOwner(user) {
		http.Error(w, "only the session owner can manage members", http.StatusForbidden)
		return nil
	}
	return sess
}

func writeMembers(w http.ResponseWriter, sess *session.Session) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"owner":   sess.OwnerEmail,
		"members": sess.Members(),
	})
}

// MembersListHandler returns the emails granted access to the session.
func MembersListHandler(w http.ResponseWriter, r *http.Request) {
	sess := requireOwner(w, r)
	if sess == nil {
		return
	}
	writeMembers(w, sess)
}

// MemberAddHandler grants a user (by email) access to the session.
func MemberAddHandler(w http.ResponseWriter, r *http.Request) {
	sess := requireOwner(w, r)
	if sess == nil {
		return
	}
	var body struct {
		Email string `json:"email"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "invalid JSON body", http.StatusBadRequest)
		return
	}
	email := strings.ToLower(strings.TrimSpace(body.Email))
	if email == "" || !strings.Contains(email, "@") {
		http.Error(w, "a valid email address is required", http.StatusBadRequest)
		return
	}
	if email == strings.ToLower(sess.OwnerEmail) {
		http.Error(w, "the owner already has access", http.StatusBadRequest)
		return
	}
	sess.AddMember(email)
	writeMembers(w, sess)
}

// MemberRemoveHandler revokes a previously granted email.
func MemberRemoveHandler(w http.ResponseWriter, r *http.Request) {
	sess := requireOwner(w, r)
	if sess == nil {
		return
	}
	email := strings.ToLower(strings.TrimSpace(r.URL.Query().Get("email")))
	if email == "" {
		http.Error(w, "email query parameter is required", http.StatusBadRequest)
		return
	}
	sess.RemoveMember(email)
	writeMembers(w, sess)
}
