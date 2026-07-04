package handlers

import (
	"net/http"

	"github.com/mirceanton/teleprompter/internal/auth"
	"github.com/mirceanton/teleprompter/internal/session"
)

// PageData is passed to every page template. In single-user mode it is the
// zero value, which keeps the templates rendering exactly as before.
type PageData struct {
	MultiUser bool
	BasePath  string
	SessionID string
	IsOwner   bool
	UserName  string
	UserEmail string
}

func pageData(r *http.Request) PageData {
	d := PageData{}
	if u, ok := auth.UserFrom(r.Context()); ok {
		d.MultiUser = true
		d.UserName = u.Name
		d.UserEmail = u.Email
		if s := sessionFrom(r); s != nil {
			d.SessionID = s.ID
			d.BasePath = "/session/" + s.ID
			d.IsOwner = s.IsOwner(u)
		}
	}
	return d
}

// HomeHandler serves "/" in multi-user mode: it lazily creates the user's
// one session and redirects into it.
func HomeHandler(m *session.Manager) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		user, ok := auth.UserFrom(r.Context())
		if !ok {
			http.Error(w, "authentication required", http.StatusUnauthorized)
			return
		}
		http.Redirect(w, r, "/session/"+m.Ensure(user).ID, http.StatusFound)
	}
}

func LandingHandler(w http.ResponseWriter, r *http.Request) {
	render(w, "landing.html", pageData(r))
}

func ControllerHandler(w http.ResponseWriter, r *http.Request) {
	render(w, "controller.html", pageData(r))
}

func TeleprompterHandler(w http.ResponseWriter, r *http.Request) {
	render(w, "teleprompter.html", pageData(r))
}
