// Package auth implements optional OIDC authentication, configured entirely
// through environment variables. When OIDC_ISSUER_URL is unset the app runs
// in single-user mode and this package is not used at all.
package auth

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/coreos/go-oidc/v3/oidc"
	"golang.org/x/oauth2"
)

const (
	sessionCookieName = "tp_auth"
	loginCookieName   = "tp_login"
	sessionTTL        = 24 * time.Hour
	loginFlowTTL      = 10 * time.Minute
)

// User identifies an authenticated OIDC user.
type User struct {
	Sub   string
	Email string
	Name  string
}

type webSession struct {
	user       User
	rawIDToken string
	expiresAt  time.Time
}

// loginFlow is the transient state of an in-progress authorization code flow,
// stored client-side in a short-lived cookie.
type loginFlow struct {
	State    string `json:"state"`
	Nonce    string `json:"nonce"`
	Verifier string `json:"verifier"`
	Next     string `json:"next"`
}

// Service performs the OIDC authorization code flow and tracks logged-in
// users via an in-memory session store keyed by an opaque cookie token.
type Service struct {
	verifier      *oidc.IDTokenVerifier
	oauth         oauth2.Config
	endSessionURL string
	postLogoutURL string
	secureCookies bool
	callbackPath  string
	mu            sync.Mutex
	sessions      map[string]*webSession
}

// NewFromEnv builds a Service from OIDC_* environment variables. It returns
// (nil, nil) when OIDC_ISSUER_URL is unset, meaning authentication is
// disabled and the app should run in single-user mode.
func NewFromEnv(ctx context.Context) (*Service, error) {
	issuer := os.Getenv("OIDC_ISSUER_URL")
	if issuer == "" {
		return nil, nil
	}

	clientID := os.Getenv("OIDC_CLIENT_ID")
	clientSecret := os.Getenv("OIDC_CLIENT_SECRET")
	redirectURL := os.Getenv("OIDC_REDIRECT_URL")
	if clientID == "" || redirectURL == "" {
		return nil, errors.New("OIDC_CLIENT_ID and OIDC_REDIRECT_URL must be set when OIDC_ISSUER_URL is set")
	}

	redirect, err := url.Parse(redirectURL)
	if err != nil || redirect.Scheme == "" || redirect.Host == "" || redirect.Path == "" {
		return nil, fmt.Errorf("OIDC_REDIRECT_URL must be an absolute URL with a path (e.g. https://example.com/auth/callback): %q", redirectURL)
	}

	scopes := strings.Fields(os.Getenv("OIDC_SCOPES"))
	if len(scopes) == 0 {
		scopes = []string{oidc.ScopeOpenID, "profile", "email"}
	}

	provider, err := oidc.NewProvider(ctx, issuer)
	if err != nil {
		return nil, fmt.Errorf("OIDC discovery failed for issuer %q: %w", issuer, err)
	}

	var extra struct {
		EndSessionEndpoint string `json:"end_session_endpoint"`
	}
	_ = provider.Claims(&extra)

	return &Service{
		verifier: provider.Verifier(&oidc.Config{ClientID: clientID}),
		oauth: oauth2.Config{
			ClientID:     clientID,
			ClientSecret: clientSecret,
			Endpoint:     provider.Endpoint(),
			RedirectURL:  redirectURL,
			Scopes:       scopes,
		},
		endSessionURL: extra.EndSessionEndpoint,
		postLogoutURL: redirect.Scheme + "://" + redirect.Host + "/",
		secureCookies: redirect.Scheme == "https",
		callbackPath:  redirect.Path,
		sessions:      make(map[string]*webSession),
	}, nil
}

// CallbackPath is the path component of OIDC_REDIRECT_URL, where the
// callback handler must be mounted.
func (s *Service) CallbackPath() string {
	return s.callbackPath
}

// LoginHandler starts the authorization code flow (with PKCE).
func (s *Service) LoginHandler(w http.ResponseWriter, r *http.Request) {
	flow := loginFlow{
		State:    randomToken(),
		Nonce:    randomToken(),
		Verifier: oauth2.GenerateVerifier(),
		Next:     safeNext(r.URL.Query().Get("next")),
	}
	payload, _ := json.Marshal(flow)
	http.SetCookie(w, &http.Cookie{
		Name:     loginCookieName,
		Value:    base64.RawURLEncoding.EncodeToString(payload),
		Path:     "/",
		MaxAge:   int(loginFlowTTL.Seconds()),
		HttpOnly: true,
		Secure:   s.secureCookies,
		SameSite: http.SameSiteLaxMode,
	})

	authURL := s.oauth.AuthCodeURL(flow.State,
		oauth2.S256ChallengeOption(flow.Verifier),
		oidc.Nonce(flow.Nonce),
	)
	http.Redirect(w, r, authURL, http.StatusFound)
}

// CallbackHandler completes the authorization code flow and establishes a
// logged-in session.
func (s *Service) CallbackHandler(w http.ResponseWriter, r *http.Request) {
	cookie, err := r.Cookie(loginCookieName)
	if err != nil {
		http.Error(w, "login flow expired, please retry", http.StatusBadRequest)
		return
	}
	s.clearCookie(w, loginCookieName)

	var flow loginFlow
	payload, err := base64.RawURLEncoding.DecodeString(cookie.Value)
	if err != nil || json.Unmarshal(payload, &flow) != nil {
		http.Error(w, "invalid login flow state", http.StatusBadRequest)
		return
	}

	if errCode := r.URL.Query().Get("error"); errCode != "" {
		http.Error(w, "authentication failed: "+errCode, http.StatusUnauthorized)
		return
	}
	if r.URL.Query().Get("state") != flow.State || flow.State == "" {
		http.Error(w, "state mismatch", http.StatusBadRequest)
		return
	}

	token, err := s.oauth.Exchange(r.Context(), r.URL.Query().Get("code"),
		oauth2.VerifierOption(flow.Verifier))
	if err != nil {
		http.Error(w, "token exchange failed", http.StatusUnauthorized)
		return
	}

	rawIDToken, ok := token.Extra("id_token").(string)
	if !ok {
		http.Error(w, "no id_token in token response", http.StatusUnauthorized)
		return
	}
	idToken, err := s.verifier.Verify(r.Context(), rawIDToken)
	if err != nil {
		http.Error(w, "invalid id_token", http.StatusUnauthorized)
		return
	}
	if idToken.Nonce != flow.Nonce {
		http.Error(w, "nonce mismatch", http.StatusUnauthorized)
		return
	}

	var claims struct {
		Email             string `json:"email"`
		Name              string `json:"name"`
		PreferredUsername string `json:"preferred_username"`
	}
	if err := idToken.Claims(&claims); err != nil {
		http.Error(w, "failed to parse claims", http.StatusUnauthorized)
		return
	}

	name := claims.Name
	if name == "" {
		name = claims.PreferredUsername
	}
	if name == "" {
		name = claims.Email
	}
	if name == "" {
		name = idToken.Subject
	}

	sessionToken := randomToken()
	s.mu.Lock()
	s.pruneLocked()
	s.sessions[sessionToken] = &webSession{
		user: User{
			Sub:   idToken.Subject,
			Email: strings.ToLower(claims.Email),
			Name:  name,
		},
		rawIDToken: rawIDToken,
		expiresAt:  time.Now().Add(sessionTTL),
	}
	s.mu.Unlock()

	http.SetCookie(w, &http.Cookie{
		Name:     sessionCookieName,
		Value:    sessionToken,
		Path:     "/",
		MaxAge:   int(sessionTTL.Seconds()),
		HttpOnly: true,
		Secure:   s.secureCookies,
		SameSite: http.SameSiteLaxMode,
	})
	http.Redirect(w, r, flow.Next, http.StatusFound)
}

// LogoutHandler terminates the local session and, when the provider
// advertises an end_session_endpoint (Keycloak does), performs RP-initiated
// logout there as well.
func (s *Service) LogoutHandler(w http.ResponseWriter, r *http.Request) {
	var rawIDToken string
	if cookie, err := r.Cookie(sessionCookieName); err == nil {
		s.mu.Lock()
		if ws, ok := s.sessions[cookie.Value]; ok {
			rawIDToken = ws.rawIDToken
			delete(s.sessions, cookie.Value)
		}
		s.mu.Unlock()
	}
	s.clearCookie(w, sessionCookieName)

	if s.endSessionURL != "" {
		if u, err := url.Parse(s.endSessionURL); err == nil {
			q := u.Query()
			if rawIDToken != "" {
				q.Set("id_token_hint", rawIDToken)
			}
			q.Set("post_logout_redirect_uri", s.postLogoutURL)
			u.RawQuery = q.Encode()
			http.Redirect(w, r, u.String(), http.StatusFound)
			return
		}
	}
	http.Redirect(w, r, "/", http.StatusFound)
}

// Middleware requires a logged-in user. Browsers asking for pages are
// redirected to the login flow; API and WebSocket requests get a plain 401.
func (s *Service) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		user, ok := s.userFor(r)
		if !ok {
			if r.Method == http.MethodGet && !strings.Contains(r.URL.Path, "/api/") {
				http.Redirect(w, r, "/auth/login?next="+url.QueryEscape(r.URL.RequestURI()), http.StatusFound)
			} else {
				http.Error(w, "authentication required", http.StatusUnauthorized)
			}
			return
		}
		next.ServeHTTP(w, r.WithContext(WithUser(r.Context(), user)))
	})
}

func (s *Service) userFor(r *http.Request) (User, bool) {
	cookie, err := r.Cookie(sessionCookieName)
	if err != nil {
		return User{}, false
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	ws, ok := s.sessions[cookie.Value]
	if !ok {
		return User{}, false
	}
	if time.Now().After(ws.expiresAt) {
		delete(s.sessions, cookie.Value)
		return User{}, false
	}
	return ws.user, true
}

func (s *Service) pruneLocked() {
	now := time.Now()
	for token, ws := range s.sessions {
		if now.After(ws.expiresAt) {
			delete(s.sessions, token)
		}
	}
}

func (s *Service) clearCookie(w http.ResponseWriter, name string) {
	http.SetCookie(w, &http.Cookie{
		Name:     name,
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
		Secure:   s.secureCookies,
		SameSite: http.SameSiteLaxMode,
	})
}

// safeNext only allows same-site absolute paths as post-login redirect
// targets, preventing open redirects.
func safeNext(next string) string {
	if strings.HasPrefix(next, "/") && !strings.HasPrefix(next, "//") && !strings.HasPrefix(next, "/\\") {
		return next
	}
	return "/"
}

func randomToken() string {
	b := make([]byte, 32)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}

type userCtxKey struct{}

// WithUser stores the authenticated user in the context.
func WithUser(ctx context.Context, u User) context.Context {
	return context.WithValue(ctx, userCtxKey{}, u)
}

// UserFrom extracts the authenticated user from the context, if any.
func UserFrom(ctx context.Context) (User, bool) {
	u, ok := ctx.Value(userCtxKey{}).(User)
	return u, ok
}
