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
