package handlers

import (
	"embed"
	"html/template"
	"log"
	"net/http"
)

var pageTemplates map[string]*template.Template

func InitTemplates(fs embed.FS) error {
	pageTemplates = make(map[string]*template.Template)
	pages := []string{"landing.html", "controller.html", "teleprompter.html"}
	for _, page := range pages {
		t, err := template.New("").ParseFS(fs, "templates/base.html", "templates/"+page)
		if err != nil {
			return err
		}
		pageTemplates[page] = t
	}
	return nil
}

func render(w http.ResponseWriter, name string, data interface{}) {
	t, ok := pageTemplates[name]
	if !ok {
		http.Error(w, "template not found", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := t.ExecuteTemplate(w, "base", data); err != nil {
		log.Printf("template render error (%s): %v", name, err)
	}
}
