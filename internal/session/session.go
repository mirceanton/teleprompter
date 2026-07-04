// Package session manages per-user teleprompter sessions for multi-user
// (OIDC) mode. Every user owns at most one session, each with its own
// isolated hub; the owner can grant other users access by email.
package session

import (
	"crypto/rand"
	"encoding/hex"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/mirceanton/teleprompter/internal/auth"
	"github.com/mirceanton/teleprompter/internal/hub"
)

// Session is one user's teleprompter room: an isolated hub plus the set of
// users allowed in.
type Session struct {
	ID         string
	OwnerSub   string
	OwnerName  string
	OwnerEmail string
	CreatedAt  time.Time
	Hub        *hub.Hub

	mu      sync.Mutex
	members map[string]struct{} // lowercased emails granted access
}

// IsOwner reports whether u owns this session.
func (s *Session) IsOwner(u auth.User) bool {
	return u.Sub == s.OwnerSub
}

// CanAccess reports whether u may enter this session.
func (s *Session) CanAccess(u auth.User) bool {
	if s.IsOwner(u) {
		return true
	}
	if u.Email == "" {
		return false
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	_, ok := s.members[strings.ToLower(u.Email)]
	return ok
}

// AddMember grants access to the user identified by email.
func (s *Session) AddMember(email string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.members[strings.ToLower(email)] = struct{}{}
}

// RemoveMember revokes access previously granted to email.
func (s *Session) RemoveMember(email string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.members, strings.ToLower(email))
}

// Members returns the emails granted access, sorted.
func (s *Session) Members() []string {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := make([]string, 0, len(s.members))
	for email := range s.members {
		out = append(out, email)
	}
	sort.Strings(out)
	return out
}

// Manager tracks all live sessions, enforcing one session per owner.
type Manager struct {
	mu      sync.Mutex
	byID    map[string]*Session
	byOwner map[string]string // owner sub -> session ID
}

// NewManager returns an empty session manager.
func NewManager() *Manager {
	return &Manager{
		byID:    make(map[string]*Session),
		byOwner: make(map[string]string),
	}
}

// Ensure returns u's session, creating it on first use.
func (m *Manager) Ensure(u auth.User) *Session {
	m.mu.Lock()
	defer m.mu.Unlock()
	if id, ok := m.byOwner[u.Sub]; ok {
		return m.byID[id]
	}
	s := &Session{
		ID:         newSessionID(),
		OwnerSub:   u.Sub,
		OwnerName:  u.Name,
		OwnerEmail: u.Email,
		CreatedAt:  time.Now(),
		Hub:        hub.New(),
		members:    make(map[string]struct{}),
	}
	m.byID[s.ID] = s
	m.byOwner[u.Sub] = s.ID
	return s
}

// Get looks a session up by ID.
func (m *Manager) Get(id string) (*Session, bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	s, ok := m.byID[id]
	return s, ok
}

// ConnectionCount sums the connections across all session hubs.
func (m *Manager) ConnectionCount() int {
	m.mu.Lock()
	sessions := make([]*Session, 0, len(m.byID))
	for _, s := range m.byID {
		sessions = append(sessions, s)
	}
	m.mu.Unlock()

	total := 0
	for _, s := range sessions {
		total += s.Hub.ConnectionCount()
	}
	return total
}

func newSessionID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
