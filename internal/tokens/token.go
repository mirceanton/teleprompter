// Package tokens implements long-lived Personal Access Tokens (PATs) that
// let a user authenticate API requests (e.g. from a Stream Deck) without
// going through the interactive OIDC browser flow. Tokens are tied to the
// OIDC subject that created them and authorize exactly what a cookie-based
// login for that user would.
package tokens

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"sync"
	"time"

	"github.com/mirceanton/teleprompter/internal/auth"
)

const tokenPrefix = "tp_pat_"

// Token is the metadata safe to return from the API/UI. It never carries the
// token secret itself.
type Token struct {
	ID         string    `json:"id"`
	Name       string    `json:"name"`
	UserSub    string    `json:"-"`
	UserEmail  string    `json:"user_email"`
	UserName   string    `json:"user_name"`
	CreatedAt  time.Time `json:"created_at"`
	LastUsedAt time.Time `json:"last_used_at,omitempty"`
}

type record struct {
	Token
	Hash string `json:"hash"`
}

// Store tracks issued tokens, optionally persisting them to a JSON file so
// they survive restarts.
type Store struct {
	mu     sync.Mutex
	path   string
	byHash map[string]*record
	byID   map[string]*record
}

type fileFormat struct {
	Tokens []*record `json:"tokens"`
}

// NewStore returns a Store. When path is empty, tokens are kept in memory
// only (lost on restart), matching the rest of the app's default behavior.
// When path is set, any existing tokens are loaded from it and every
// create/revoke persists the file; a missing file is not an error.
func NewStore(path string) (*Store, error) {
	s := &Store{
		path:   path,
		byHash: make(map[string]*record),
		byID:   make(map[string]*record),
	}
	if path == "" {
		return s, nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return s, nil
		}
		return nil, fmt.Errorf("reading token file %q: %w", path, err)
	}
	var ff fileFormat
	if err := json.Unmarshal(data, &ff); err != nil {
		return nil, fmt.Errorf("parsing token file %q: %w", path, err)
	}
	for _, rec := range ff.Tokens {
		s.byHash[rec.Hash] = rec
		s.byID[rec.ID] = rec
	}
	return s, nil
}

// Create mints a new token for u, returning the raw secret (shown to the
// caller exactly once) and its safe metadata.
func (s *Store) Create(u auth.User, name string) (raw string, meta Token, err error) {
	raw = tokenPrefix + randomToken()
	rec := &record{
		Token: Token{
			ID:        randomID(),
			Name:      name,
			UserSub:   u.Sub,
			UserEmail: u.Email,
			UserName:  u.Name,
			CreatedAt: time.Now(),
		},
		Hash: hash(raw),
	}

	s.mu.Lock()
	s.byHash[rec.Hash] = rec
	s.byID[rec.ID] = rec
	persistErr := s.persistLocked()
	s.mu.Unlock()

	if persistErr != nil {
		return "", Token{}, persistErr
	}
	return raw, rec.Token, nil
}

// Verify reports whether raw is a currently-valid token, returning the user
// it was issued to. LastUsedAt is updated in memory only, best-effort, and
// is not persisted on every call to avoid disk writes on the hot path.
func (s *Store) Verify(raw string) (auth.User, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	rec, ok := s.byHash[hash(raw)]
	if !ok {
		return auth.User{}, false
	}
	rec.LastUsedAt = time.Now()
	return auth.User{Sub: rec.UserSub, Email: rec.UserEmail, Name: rec.UserName}, true
}

// List returns sub's tokens, oldest first.
func (s *Store) List(sub string) []Token {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := make([]Token, 0)
	for _, rec := range s.byID {
		if rec.UserSub == sub {
			out = append(out, rec.Token)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].CreatedAt.Before(out[j].CreatedAt) })
	return out
}

// Revoke deletes the token id if it belongs to sub, reporting whether
// anything was removed.
func (s *Store) Revoke(sub, id string) (bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	rec, ok := s.byID[id]
	if !ok || rec.UserSub != sub {
		return false, nil
	}
	delete(s.byID, id)
	delete(s.byHash, rec.Hash)
	if err := s.persistLocked(); err != nil {
		return false, err
	}
	return true, nil
}

func (s *Store) persistLocked() error {
	if s.path == "" {
		return nil
	}
	recs := make([]*record, 0, len(s.byID))
	for _, rec := range s.byID {
		recs = append(recs, rec)
	}
	data, err := json.MarshalIndent(fileFormat{Tokens: recs}, "", "  ")
	if err != nil {
		return err
	}
	tmp := s.path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o600); err != nil {
		return fmt.Errorf("writing token file %q: %w", tmp, err)
	}
	if err := os.Rename(tmp, s.path); err != nil {
		return fmt.Errorf("saving token file %q: %w", s.path, err)
	}
	return nil
}

func hash(raw string) string {
	sum := sha256.Sum256([]byte(raw))
	return hex.EncodeToString(sum[:])
}

func randomToken() string {
	b := make([]byte, 32)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}

func randomID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
