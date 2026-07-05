package main

import (
	"context"
	"embed"
	"log"
	"net/http"
	"os"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/mirceanton/teleprompter/internal/auth"
	"github.com/mirceanton/teleprompter/internal/handlers"
	"github.com/mirceanton/teleprompter/internal/hub"
	"github.com/mirceanton/teleprompter/internal/session"
)

//go:embed templates
var templateFS embed.FS

// hubRoutes registers the routes that operate on the hub resolved from the
// request context: the WebSocket endpoint and the playback REST API.
func hubRoutes(r chi.Router) {
	r.Get("/api/ws", handlers.WebSocketHandler())

	r.Post("/api/playback/start", handlers.PlaybackBroadcast(`{"type":"start"}`))
	r.Post("/api/playback/stop", handlers.PlaybackBroadcast(`{"type":"pause"}`))
	r.Post("/api/playback/scroll/top", handlers.PlaybackBroadcast(`{"type":"go_to_beginning"}`))
	r.Post("/api/playback/scroll/beginning", handlers.PlaybackBroadcast(`{"type":"go_to_beginning"}`))
	r.Post("/api/playback/scroll/back", handlers.ScrollLines("backward", 5))
	r.Post("/api/playback/scroll/back/{lines}", handlers.ScrollLinesParam("backward"))
	r.Post("/api/playback/scroll/forward", handlers.ScrollLines("forward", 5))
	r.Post("/api/playback/scroll/forward/{lines}", handlers.ScrollLinesParam("forward"))
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	if err := handlers.InitTemplates(templateFS); err != nil {
		log.Fatalf("failed to load templates: %v", err)
	}

	authSvc, err := auth.NewFromEnv(context.Background())
	if err != nil {
		log.Fatalf("OIDC configuration error: %v", err)
	}

	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/api/live", handlers.LiveHandler)

	if authSvc == nil {
		// Single-user mode: no authentication, one global hub shared by
		// everyone, same behavior and routes as always.
		log.Println("OIDC not configured; running in single-user mode")
		h := hub.New()

		r.Get("/api/health", handlers.HealthHandler(h))
		r.Get("/", handlers.LandingHandler)
		r.Get("/controller", handlers.ControllerHandler)
		r.Get("/teleprompter", handlers.TeleprompterHandler)
		r.Group(func(r chi.Router) {
			r.Use(handlers.WithHub(h))
			hubRoutes(r)
		})
	} else {
		// Multi-user mode: OIDC login required, one isolated session per
		// user under /session/{id}, joinable by invitation only.
		log.Println("OIDC configured; running in multi-user mode")
		mgr := session.NewManager()

		r.Get("/api/health", handlers.HealthHandler(mgr))
		r.Get("/auth/login", authSvc.LoginHandler)
		r.Get(authSvc.CallbackPath(), authSvc.CallbackHandler)
		r.Get("/auth/logout", authSvc.LogoutHandler)

		r.Group(func(r chi.Router) {
			r.Use(authSvc.Middleware)
			r.Get("/", handlers.HomeHandler(mgr))
			r.Route("/session/{sessionID}", func(r chi.Router) {
				r.Use(handlers.SessionAccess(mgr))
				r.Get("/", handlers.LandingHandler)
				r.Get("/controller", handlers.ControllerHandler)
				r.Get("/teleprompter", handlers.TeleprompterHandler)
				r.Get("/api/members", handlers.MembersListHandler)
				r.Post("/api/members", handlers.MemberAddHandler)
				r.Delete("/api/members", handlers.MemberRemoveHandler)
				hubRoutes(r)
			})
		})
	}

	log.Printf("teleprompter listening on :%s", port)
	if err := http.ListenAndServe(":"+port, r); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
