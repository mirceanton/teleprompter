package handlers

import "net/http"

func LandingHandler(w http.ResponseWriter, r *http.Request) {
	render(w, "landing.html", nil)
}

func ControllerHandler(w http.ResponseWriter, r *http.Request) {
	render(w, "controller.html", nil)
}

func TeleprompterHandler(w http.ResponseWriter, r *http.Request) {
	render(w, "teleprompter.html", nil)
}
