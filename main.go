package main

import (
	"embed"
	"log"
	"net/http"
	"os"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/mirceanton/teleprompter/internal/handlers"
	"github.com/mirceanton/teleprompter/internal/hub"
)

//go:embed templates
var templateFS embed.FS

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	h := hub.New()

	if err := handlers.InitTemplates(templateFS); err != nil {
		log.Fatalf("failed to load templates: %v", err)
	}

	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/", handlers.LandingHandler)
	r.Get("/controller", handlers.ControllerHandler)
	r.Get("/teleprompter", handlers.TeleprompterHandler)

	r.Get("/api/ws", handlers.WebSocketHandler(h))
	r.Get("/api/health", handlers.HealthHandler(h))
	r.Get("/api/live", handlers.LiveHandler)

	r.Post("/api/playback/start", handlers.PlaybackBroadcast(h, `{"type":"start"}`))
	r.Post("/api/playback/stop", handlers.PlaybackBroadcast(h, `{"type":"pause"}`))
	r.Post("/api/playback/scroll/top", handlers.PlaybackBroadcast(h, `{"type":"go_to_beginning"}`))
	r.Post("/api/playback/scroll/beginning", handlers.PlaybackBroadcast(h, `{"type":"go_to_beginning"}`))
	r.Post("/api/playback/scroll/back", handlers.ScrollLines(h, "backward", 5))
	r.Post("/api/playback/scroll/back/{lines}", handlers.ScrollLinesParam(h, "backward"))
	r.Post("/api/playback/scroll/forward", handlers.ScrollLines(h, "forward", 5))
	r.Post("/api/playback/scroll/forward/{lines}", handlers.ScrollLinesParam(h, "forward"))

	log.Printf("teleprompter listening on :%s", port)
	if err := http.ListenAndServe(":"+port, r); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
