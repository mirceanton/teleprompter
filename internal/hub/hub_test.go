package hub

import (
	"encoding/json"
	"testing"
)

// drain discards any messages currently queued on ch, without blocking.
func drain(ch chan []byte) {
	for {
		select {
		case <-ch:
		default:
			return
		}
	}
}

// readOne reads the next queued message off ch and decodes it as JSON. It
// fails the test if no message is queued, since every send in these tests
// happens synchronously before the read.
func readOne(t *testing.T, ch chan []byte) map[string]interface{} {
	t.Helper()
	select {
	case data := <-ch:
		var msg map[string]interface{}
		if err := json.Unmarshal(data, &msg); err != nil {
			t.Fatalf("unmarshal message: %v", err)
		}
		return msg
	default:
		t.Fatal("expected a message on the channel, got none")
		return nil
	}
}

func TestSendStateRehydratesScript(t *testing.T) {
	h := New()
	h.SetScript("hello world")

	ctrl := h.Register(nil)
	drain(ctrl.Send)

	h.SendState(ctrl.ID)

	msg := readOne(t, ctrl.Send)
	if msg["type"] != "state_sync" {
		t.Fatalf("type = %v, want %q", msg["type"], "state_sync")
	}
	if msg["script"] != "hello world" {
		t.Fatalf("script = %v, want %q", msg["script"], "hello world")
	}
	if msg["has_script"] != true {
		t.Fatalf("has_script = %v, want true", msg["has_script"])
	}
}

func TestSendStateWithNoScriptYet(t *testing.T) {
	h := New()

	ctrl := h.Register(nil)
	drain(ctrl.Send)

	h.SendState(ctrl.ID)

	msg := readOne(t, ctrl.Send)
	if msg["script"] != "" {
		t.Fatalf("script = %v, want empty string", msg["script"])
	}
	if msg["has_script"] != false {
		t.Fatalf("has_script = %v, want false so the client doesn't mistake a never-set script for a legitimately-cleared one", msg["has_script"])
	}
}

func TestSendStateAfterLegitimatelyClearedScript(t *testing.T) {
	h := New()
	h.SetScript("hello world")
	h.SetScript("")

	ctrl := h.Register(nil)
	drain(ctrl.Send)

	h.SendState(ctrl.ID)

	msg := readOne(t, ctrl.Send)
	if msg["script"] != "" {
		t.Fatalf("script = %v, want empty string", msg["script"])
	}
	if msg["has_script"] != true {
		t.Fatalf("has_script = %v, want true — an intentionally-cleared script should still converge on the client", msg["has_script"])
	}
}

func TestSetScriptFromControllerRequiresControllerRole(t *testing.T) {
	h := New()
	prompter := h.Register(nil)
	ctrl := h.Register(nil)
	drain(prompter.Send)
	drain(ctrl.Send)

	// prompter has no role set (never sent `mode: teleprompter` through
	// UpdateRole in this test), so this must not persist.
	h.SetScriptFromController(prompter.ID, "sneaky overwrite")

	h.SendState(ctrl.ID)
	msg := readOne(t, ctrl.Send)
	if msg["has_script"] != false {
		t.Fatalf("has_script = %v, want false: a non-controller's text message must not persist", msg["has_script"])
	}

	h.UpdateRole(ctrl.ID, "controller")
	drain(ctrl.Send) // discard the participants_update broadcast from UpdateRole

	h.SetScriptFromController(ctrl.ID, "legitimate update")

	h.SendState(ctrl.ID)
	msg = readOne(t, ctrl.Send)
	if msg["script"] != "legitimate update" {
		t.Fatalf("script = %v, want %q", msg["script"], "legitimate update")
	}
}

func TestSendStateIncludesRecordedSettings(t *testing.T) {
	h := New()
	prompter := h.Register(nil)
	ctrl := h.Register(nil)
	drain(prompter.Send)
	drain(ctrl.Send)

	h.RecordSetting(prompter.ID, "speed", map[string]interface{}{"value": 1.5})
	h.RecordSetting(prompter.ID, "width", map[string]interface{}{"value": float64(80)})
	h.RecordSetting(prompter.ID, "font_size", map[string]interface{}{"value": 3.0})
	h.RecordSetting(prompter.ID, "lines_per_step", map[string]interface{}{"value": float64(3)})
	h.RecordSetting(prompter.ID, "mirror", map[string]interface{}{"horizontal": true, "vertical": false})

	h.SendState(ctrl.ID)
	msg := readOne(t, ctrl.Send)

	settings, ok := msg["settings"].(map[string]interface{})
	if !ok {
		t.Fatalf("settings missing or wrong type: %#v", msg["settings"])
	}
	snap, ok := settings[prompter.ID].(map[string]interface{})
	if !ok {
		t.Fatalf("no settings snapshot for prompter %s: %#v", prompter.ID, settings)
	}

	want := map[string]interface{}{
		"scrollSpeed":      1.5,
		"textWidth":        float64(80),
		"fontSize":         3.0,
		"linesPerStep":     float64(3),
		"horizontalMirror": true,
	}
	for k, v := range want {
		if snap[k] != v {
			t.Errorf("settings[%s] = %v, want %v", k, snap[k], v)
		}
	}
}

func TestRecordSettingIgnoresUnknownParticipant(t *testing.T) {
	h := New()
	ctrl := h.Register(nil)
	drain(ctrl.Send)

	h.RecordSetting("does-not-exist", "speed", map[string]interface{}{"value": 2.0})

	h.SendState(ctrl.ID)
	msg := readOne(t, ctrl.Send)
	settings, _ := msg["settings"].(map[string]interface{})
	if len(settings) != 0 {
		t.Fatalf("settings = %#v, want empty", settings)
	}
}

func TestRecordSettingIgnoresUnknownMessageType(t *testing.T) {
	h := New()
	prompter := h.Register(nil)
	ctrl := h.Register(nil)
	drain(prompter.Send)
	drain(ctrl.Send)

	h.RecordSetting(prompter.ID, "go_to_beginning", map[string]interface{}{"value": 2.0})

	h.SendState(ctrl.ID)
	msg := readOne(t, ctrl.Send)
	settings, _ := msg["settings"].(map[string]interface{})
	if len(settings) != 0 {
		t.Fatalf("settings = %#v, want empty", settings)
	}
}

func TestUnregisterClearsSettings(t *testing.T) {
	h := New()
	prompter := h.Register(nil)
	ctrl := h.Register(nil)
	drain(prompter.Send)
	drain(ctrl.Send)

	h.RecordSetting(prompter.ID, "speed", map[string]interface{}{"value": 2.0})
	h.Unregister(prompter)
	drain(ctrl.Send) // discard the participant_left broadcast

	h.SendState(ctrl.ID)
	msg := readOne(t, ctrl.Send)
	settings, _ := msg["settings"].(map[string]interface{})
	if len(settings) != 0 {
		t.Fatalf("settings = %#v, want empty after unregister", settings)
	}
}

func TestSetScriptOverwritesPreviousValue(t *testing.T) {
	h := New()
	h.SetScript("first draft")
	h.SetScript("second draft")

	ctrl := h.Register(nil)
	drain(ctrl.Send)

	h.SendState(ctrl.ID)
	msg := readOne(t, ctrl.Send)
	if msg["script"] != "second draft" {
		t.Fatalf("script = %v, want %q", msg["script"], "second draft")
	}
}

func TestSendTeleprompterStateRehydratesScriptMarkdownAndPlayback(t *testing.T) {
	h := New()
	ctrl := h.Register(nil)
	prompter := h.Register(nil)
	drain(ctrl.Send)
	drain(prompter.Send)

	h.UpdateRole(ctrl.ID, "controller")
	drain(ctrl.Send)
	drain(prompter.Send) // discard the participants_update broadcast

	h.SetScriptFromController(ctrl.ID, "hello world")
	h.SetMarkdownFromController(ctrl.ID, true)
	h.SetPlaybackFromController(ctrl.ID, "start")

	h.SendTeleprompterState(prompter.ID)
	msg := readOne(t, prompter.Send)

	if msg["type"] != "state_sync" {
		t.Fatalf("type = %v, want %q", msg["type"], "state_sync")
	}
	if msg["script"] != "hello world" {
		t.Fatalf("script = %v, want %q", msg["script"], "hello world")
	}
	if msg["has_script"] != true {
		t.Fatalf("has_script = %v, want true", msg["has_script"])
	}
	if msg["markdown_enabled"] != true {
		t.Fatalf("markdown_enabled = %v, want true", msg["markdown_enabled"])
	}
	if msg["is_playing"] != true {
		t.Fatalf("is_playing = %v, want true", msg["is_playing"])
	}
	if msg["at_end"] != false {
		t.Fatalf("at_end = %v, want false", msg["at_end"])
	}
}

func TestSendTeleprompterStateWithNoScriptYet(t *testing.T) {
	h := New()
	prompter := h.Register(nil)
	drain(prompter.Send)

	h.SendTeleprompterState(prompter.ID)
	msg := readOne(t, prompter.Send)

	if msg["script"] != "" {
		t.Fatalf("script = %v, want empty string", msg["script"])
	}
	if msg["has_script"] != false {
		t.Fatalf("has_script = %v, want false", msg["has_script"])
	}
	if msg["markdown_enabled"] != false {
		t.Fatalf("markdown_enabled = %v, want false", msg["markdown_enabled"])
	}
	if msg["is_playing"] != false {
		t.Fatalf("is_playing = %v, want false", msg["is_playing"])
	}
	if msg["at_end"] != false {
		t.Fatalf("at_end = %v, want false", msg["at_end"])
	}
}

func TestSendTeleprompterStateIncludesOnlyOwnSettings(t *testing.T) {
	h := New()
	prompterA := h.Register(nil)
	prompterB := h.Register(nil)
	drain(prompterA.Send)
	drain(prompterB.Send)

	h.RecordSetting(prompterA.ID, "speed", map[string]interface{}{"value": 1.5})
	h.RecordSetting(prompterB.ID, "speed", map[string]interface{}{"value": 2.5})

	h.SendTeleprompterState(prompterA.ID)
	msg := readOne(t, prompterA.Send)

	settings, ok := msg["settings"].(map[string]interface{})
	if !ok {
		t.Fatalf("settings missing or wrong type: %#v", msg["settings"])
	}
	if settings["scrollSpeed"] != 1.5 {
		t.Fatalf("settings[scrollSpeed] = %v, want 1.5", settings["scrollSpeed"])
	}
	if _, ok := settings["id"]; ok {
		t.Fatalf("settings = %#v, want a flat snapshot for prompterA only, not keyed by participant ID", settings)
	}
}

func TestSetMarkdownFromControllerRequiresControllerRole(t *testing.T) {
	h := New()
	prompter := h.Register(nil)
	drain(prompter.Send)

	// prompter has no role set, so this must not persist.
	h.SetMarkdownFromController(prompter.ID, true)

	h.SendTeleprompterState(prompter.ID)
	msg := readOne(t, prompter.Send)
	if msg["markdown_enabled"] != false {
		t.Fatalf("markdown_enabled = %v, want false: a non-controller's markdown message must not persist", msg["markdown_enabled"])
	}
}

func TestSetPlaybackFromControllerRequiresControllerRole(t *testing.T) {
	h := New()
	prompter := h.Register(nil)
	drain(prompter.Send)

	// prompter has no role set, so this must not persist.
	h.SetPlaybackFromController(prompter.ID, "start")

	h.SendTeleprompterState(prompter.ID)
	msg := readOne(t, prompter.Send)
	if msg["is_playing"] != false {
		t.Fatalf("is_playing = %v, want false: a non-controller's playback message must not persist", msg["is_playing"])
	}
}

func TestSetPlaybackFromControllerTracksPositionAndPlayState(t *testing.T) {
	h := New()
	ctrl := h.Register(nil)
	prompter := h.Register(nil)
	drain(ctrl.Send)
	drain(prompter.Send)

	h.UpdateRole(ctrl.ID, "controller")
	drain(ctrl.Send)
	drain(prompter.Send)

	h.SetPlaybackFromController(ctrl.ID, "start")
	h.SendTeleprompterState(prompter.ID)
	msg := readOne(t, prompter.Send)
	if msg["is_playing"] != true {
		t.Fatalf("is_playing = %v, want true after start", msg["is_playing"])
	}

	h.SetPlaybackFromController(ctrl.ID, "go_to_end")
	h.SendTeleprompterState(prompter.ID)
	msg = readOne(t, prompter.Send)
	if msg["is_playing"] != false {
		t.Fatalf("is_playing = %v, want false after go_to_end", msg["is_playing"])
	}
	if msg["at_end"] != true {
		t.Fatalf("at_end = %v, want true after go_to_end", msg["at_end"])
	}

	h.SetPlaybackFromController(ctrl.ID, "go_to_beginning")
	h.SendTeleprompterState(prompter.ID)
	msg = readOne(t, prompter.Send)
	if msg["at_end"] != false {
		t.Fatalf("at_end = %v, want false after go_to_beginning", msg["at_end"])
	}
}

func TestSetPlaybackFromControllerStartClearsAtEnd(t *testing.T) {
	h := New()
	ctrl := h.Register(nil)
	prompter := h.Register(nil)
	drain(ctrl.Send)
	drain(prompter.Send)

	h.UpdateRole(ctrl.ID, "controller")
	drain(ctrl.Send)
	drain(prompter.Send)

	// go_to_end followed by start (e.g. a controller parking the prompter at
	// the end, then resuming playback) must not leave atEnd and isPlaying
	// both true: a newly-connecting teleprompter's applyStateSync() treats
	// "at rest at the end" and "actively scrolling" as mutually exclusive,
	// and running both goToEnd() and startScrolling() at once fights over
	// scrollPos.
	h.SetPlaybackFromController(ctrl.ID, "go_to_end")
	h.SetPlaybackFromController(ctrl.ID, "start")

	h.SendTeleprompterState(prompter.ID)
	msg := readOne(t, prompter.Send)
	if msg["is_playing"] != true {
		t.Fatalf("is_playing = %v, want true after start", msg["is_playing"])
	}
	if msg["at_end"] != false {
		t.Fatalf("at_end = %v, want false after start clears the parked-at-end position", msg["at_end"])
	}
}

func TestSetScriptFromControllerResetsPlaybackState(t *testing.T) {
	h := New()
	ctrl := h.Register(nil)
	prompter := h.Register(nil)
	drain(ctrl.Send)
	drain(prompter.Send)

	h.UpdateRole(ctrl.ID, "controller")
	drain(ctrl.Send)
	drain(prompter.Send)

	h.SetPlaybackFromController(ctrl.ID, "start")
	h.SetPlaybackFromController(ctrl.ID, "go_to_end")

	// A fresh script push resets playback client-side on every teleprompter,
	// so the hub's retained state should follow suit.
	h.SetScriptFromController(ctrl.ID, "a new script")

	h.SendTeleprompterState(prompter.ID)
	msg := readOne(t, prompter.Send)
	if msg["is_playing"] != false {
		t.Fatalf("is_playing = %v, want false after a new script is set", msg["is_playing"])
	}
	if msg["at_end"] != false {
		t.Fatalf("at_end = %v, want false after a new script is set", msg["at_end"])
	}
}
