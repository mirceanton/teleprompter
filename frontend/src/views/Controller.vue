<template>
  <v-app theme="dark">
    <v-app-bar app elevation="16" height="64" color="grey-darken-4">
      <v-container fluid class="d-flex align-center">
        <div class="d-flex align-center">
          <v-icon color="teal" size="32" class="mr-3"
            >mdi-presentation-play</v-icon
          >
          <div class="text-h5 font-weight-bold">Teleprompter</div>
        </div>
        <v-spacer></v-spacer>
        <v-btn prepend-icon="mdi-logout" @click="exitTeleprompter">
          Leave Room
        </v-btn>
      </v-container>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-0 fill-height">
        <v-row no-gutters class="fill-height">
          <!-- Left Side - Script Editor -->
          <v-col cols="12" lg="8" xl="9" class="d-flex flex-column">
            <div class="script-editor-section pa-6 d-flex flex-column">
              <!-- Script Editor Header -->
              <div class="d-flex align-center justify-space-between mb-4">
                <h2 class="text-h6 font-weight-bold">Script Editor</h2>
                <div class="d-flex align-center gap-3">
                  <v-btn
                    class="mr-2"
                    variant="outlined"
                    size="small"
                    prepend-icon="mdi-undo"
                    @click="undoScript"
                  >
                    Undo
                  </v-btn>
                  <v-btn
                    class="ml-2"
                    variant="outlined"
                    size="small"
                    prepend-icon="mdi-redo"
                    @click="redoScript"
                  >
                    Redo
                  </v-btn>
                </div>
              </div>

              <!-- Script Editor Textarea -->
              <div class="script-editor-container flex-grow-1 mb-2">
                <v-textarea
                  v-model="scriptText"
                  variant="outlined"
                  class="script-textarea fill-height"
                  hide-details
                  @input="debouncedSyncText"
                  @keydown="handleKeyboardShortcuts"
                />
              </div>

              <!-- Script Status Footer -->
              <div class="script-status-footer pl-4 pr-4 pt-2 pb-2 bg-grey-darken-4">
                <div class="d-flex align-center justify-space-between">
                  <div class="d-flex align-center gap-4">
                    <span class="text-caption text-medium-emphasis">
                      {{ characterCount }} characters · {{ wordCount }} words
                    </span>
                  </div>
                  <v-spacer></v-spacer>
                  <span class="text-caption text-medium-emphasis mr-8">
                    Last update: {{ lastSyncTime }}
                  </span>
                  <v-btn
                    variant="outlined"
                    size="small"
                    prepend-icon="mdi-sync"
                    @click="syncScript"
                  >
                    Sync now
                  </v-btn>
                </div>
              </div>
            </div>
          </v-col>

          <!-- Right Sidebar - Controls -->
          <v-col cols="12" lg="4" xl="3" class="sidebar">
            <div class="controls-sidebar pa-6 d-flex flex-column">
              <!-- Playback Controls Section -->
              <div class="control-section mb-8">
                <h3 class="text-h6 font-weight-bold mb-6">Playback Controls</h3>

                <!-- Large Circular Playback Buttons -->
                <div class="d-flex justify-center align-center mb-6">
                  <v-btn
                    icon
                    size="48"
                    color="teal"
                    variant="flat"
                    class="control-btn mr-4"
                    @click="goToBeginning"
                  >
                    <v-icon size="20">mdi-skip-backward</v-icon>
                  </v-btn>

                  <v-btn
                    icon
                    size="64"
                    color="teal"
                    variant="flat"
                    class="control-btn mr-4"
                    @click="handleBackwardClick"
                  >
                    <v-icon size="24">mdi-step-backward</v-icon>
                  </v-btn>

                  <v-btn
                    icon
                    size="100"
                    :color="isPlaying ? 'error' : 'success'"
                    variant="flat"
                    class="play-btn mr-4"
                    @click="togglePlayback"
                  >
                    <v-icon size="40">{{
                      isPlaying ? "mdi-pause" : "mdi-play"
                    }}</v-icon>
                  </v-btn>

                  <v-btn
                    icon
                    size="64"
                    color="teal"
                    variant="flat"
                    class="control-btn mr-4"
                    @click="handleForwardClick"
                  >
                    <v-icon size="24">mdi-step-forward</v-icon>
                  </v-btn>

                  <v-btn
                    icon
                    size="48"
                    color="teal"
                    variant="flat"
                    class="control-btn"
                    @click="goToEnd"
                  >
                    <v-icon size="20">mdi-skip-forward</v-icon>
                  </v-btn>
                </div>

                <!-- Markdown Toggle -->
                <div class="d-flex">
                  <v-btn
                    :color="markdownEnabled ? 'teal' : 'grey-darken-2'"
                    :variant='outlined'
                    size="medium"
                    class="flex-grow-1 pt-2 pb-2"
                    :prepend-icon="markdownEnabled ? 'mdi-language-markdown' : 'mdi-format-text'"
                    @click="toggleMarkdown"
                  >
                    {{ markdownEnabled ? 'Markdown' : 'Plain Text' }}
                  </v-btn>
                </div>
              </div>

              <!-- Teleprompters Section (Per-Prompter Settings) -->
              <div class="control-section flex-grow-1 d-flex flex-column">
                <h3 class="text-h6 font-weight-bold mb-6">Teleprompters</h3>
                <div class="participants-container flex-grow-1">
                  <div
                    v-if="teleprompterParticipants.length === 0"
                    class="text-center text-medium-emphasis pa-6"
                  >
                    <v-icon size="48" class="mb-3 text-grey-darken-1">mdi-monitor</v-icon>
                    <div class="text-body-2 mb-1">No teleprompters connected</div>
                    <div class="text-caption">Waiting for devices to join...</div>
                  </div>

                  <div v-else class="prompter-list">
                    <div
                      v-for="participant in teleprompterParticipants"
                      :key="participant.id"
                      class="prompter-card"
                    >
                      <!-- Prompter Header (Collapsible) -->
                      <div
                        class="prompter-header d-flex align-center pa-3"
                        @click="togglePrompterExpanded(participant.id)"
                      >
                        <v-icon color="green" size="20" class="mr-3">mdi-monitor</v-icon>
                        <div class="flex-grow-1">
                          <div class="prompter-name">
                            Teleprompter #{{ getPrompterIndex(participant.id) }}
                          </div>
                          <div class="prompter-time text-caption text-medium-emphasis">
                            Joined {{ formatTime(participant.joined_at) }}
                          </div>
                        </div>
                        <v-icon size="16" color="success" class="mr-2">mdi-circle</v-icon>
                        <v-icon size="20">
                          {{ isPrompterExpanded(participant.id) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                        </v-icon>
                      </div>

                      <!-- Prompter Settings (Expandable) -->
                      <v-expand-transition>
                        <div v-show="isPrompterExpanded(participant.id)" class="prompter-settings pa-3">
                          <!-- Speed -->
                          <div class="control-group mb-3">
                            <label class="text-caption text-medium-emphasis mb-1 d-block">
                              Playback Speed
                            </label>
                            <div class="d-flex align-center gap-2">
                              <v-btn
                                icon="mdi-minus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterSpeed(participant.id, -0.1)"
                              />
                              <v-text-field
                                :model-value="getPrompterSettings(participant.id).scrollSpeed.toFixed(1) + 'x'"
                                readonly
                                variant="solo-filled"
                                hide-details
                                density="compact"
                                class="text-center"
                              />
                              <v-btn
                                icon="mdi-plus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterSpeed(participant.id, 0.1)"
                              />
                            </div>
                          </div>

                          <!-- Lines per Step -->
                          <div class="control-group mb-3">
                            <label class="text-caption text-medium-emphasis mb-1 d-block">
                              Lines to Scroll
                            </label>
                            <div class="d-flex align-center gap-2">
                              <v-btn
                                icon="mdi-minus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterLinesPerStep(participant.id, -1)"
                              />
                              <v-text-field
                                :model-value="getPrompterSettings(participant.id).linesPerStep"
                                readonly
                                variant="solo-filled"
                                hide-details
                                density="compact"
                                class="text-center"
                              />
                              <v-btn
                                icon="mdi-plus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterLinesPerStep(participant.id, 1)"
                              />
                            </div>
                          </div>

                          <!-- Text Width -->
                          <div class="control-group mb-3">
                            <label class="text-caption text-medium-emphasis mb-1 d-block">
                              Text Width
                            </label>
                            <div class="d-flex align-center gap-2">
                              <v-btn
                                icon="mdi-minus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterWidth(participant.id, -5)"
                              />
                              <v-text-field
                                :model-value="getPrompterSettings(participant.id).textWidth + '%'"
                                readonly
                                variant="solo-filled"
                                hide-details
                                density="compact"
                                class="text-center"
                              />
                              <v-btn
                                icon="mdi-plus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterWidth(participant.id, 5)"
                              />
                            </div>
                          </div>

                          <!-- Font Size -->
                          <div class="control-group mb-3">
                            <label class="text-caption text-medium-emphasis mb-1 d-block">
                              Font Size
                            </label>
                            <div class="d-flex align-center gap-2">
                              <v-btn
                                icon="mdi-minus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterFontSize(participant.id, -0.1)"
                              />
                              <v-text-field
                                :model-value="getPrompterSettings(participant.id).fontSize.toFixed(1) + 'em'"
                                readonly
                                variant="solo-filled"
                                hide-details
                                density="compact"
                                class="text-center"
                              />
                              <v-btn
                                icon="mdi-plus"
                                size="x-small"
                                variant="outlined"
                                @click="adjustPrompterFontSize(participant.id, 0.1)"
                              />
                            </div>
                          </div>

                          <!-- Mirroring -->
                          <div class="control-group">
                            <label class="text-caption text-medium-emphasis mb-1 d-block">
                              Mirroring
                            </label>
                            <div class="d-flex gap-2">
                              <v-btn
                                :color="getPrompterSettings(participant.id).verticalMirror ? 'teal' : 'grey-darken-2'"
                                :variant="getPrompterSettings(participant.id).verticalMirror ? 'flat' : 'outlined'"
                                size="small"
                                class="flex-grow-1"
                                @click="togglePrompterVerticalMirror(participant.id)"
                              >
                                Vertical
                              </v-btn>
                              <v-btn
                                :color="getPrompterSettings(participant.id).horizontalMirror ? 'teal' : 'grey-darken-2'"
                                :variant="getPrompterSettings(participant.id).horizontalMirror ? 'flat' : 'outlined'"
                                size="small"
                                class="flex-grow-1"
                                @click="togglePrompterHorizontalMirror(participant.id)"
                              >
                                Horizontal
                              </v-btn>
                            </div>
                          </div>
                        </div>
                      </v-expand-transition>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false"> Close </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script>
import { config } from "@/utils/config.js";
import QRCode from "qrcode";

export default {
  name: "Controller",

  data() {
    return {
      // Connection state
      ws: null,
      channelName: "",
      roomCredentials: null,
      participantId: null,
      participants: [],
      connectionInfo: {
        show: false,
        count: 0,
      },

      // Per-prompter settings (keyed by participant ID)
      prompterSettings: {},

      // Room management UI
      showRoomInfoDialog: false,
      editableRoomName: "",
      showSecret: false,
      qrCodeDataUrl: null,

      // UI state for new design
      showDrawer: false,
      lastSyncTime: "Never",
      expandedPrompters: {},  // Track which prompter settings are expanded

      // Script content
      scriptText: `# Welcome to Remote Teleprompter!

This is your teleprompter script. Edit this text on your computer, and it will appear on your phone's screen.

Use the controls to start, pause, and navigate through your script with smooth scrolling.

Instructions:
1. Use the same channel name on all devices
2. Select "Controller Mode" on your computer
3. Select "Teleprompter Mode" on your phones/tablets
4. Click "Start" to begin scrolling

Features:
- Play/Pause controls for smooth teleprompter operation
- Scroll forward/backward by customizable number of lines
- Jump to beginning or end of script instantly
- Adjustable text size, width, and scrolling speed
- Mirror settings for camera setups

Multi-Camera Support:
This application supports multiple teleprompter devices connected to the same channel, perfect for multi-camera setups.

Happy teleprompting! 🎬`,

      // Global control settings (affects all prompters when changed in global section)
      scrollSpeed: 1.0,
      textWidth: 100,
      fontSize: 2.5,
      horizontalMirror: false,
      verticalMirror: false,
      linesPerStep: 5,
      markdownEnabled: false,

      // Navigation settings
      isPlaying: false,
      currentScrollPosition: 0, // Track current scroll position in lines

      // UI state
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },

      // Debounce timer
      syncTimeout: null,

      // Undo/Redo functionality
      undoStack: [],
      redoStack: [],
      isUndoRedoOperation: false,
      lastScriptValue: "",

      // Connection tracking
      lastConnectionCount: 0,
    };
  },

  computed: {
    scriptEditorStyle() {
      // Mac width constraints for wider displays
      return {
        maxWidth: "1200px",
        margin: "0 auto",
        width: "100%",
      };
    },

    joinUrl() {
      if (!this.roomCredentials) return "";
      const baseUrl = window.location.origin;
      const credentials = {
        room_id: this.roomCredentials.room_id,
        room_secret: this.roomCredentials.room_secret,
      };
      return `${baseUrl}/?join=${encodeURIComponent(
        JSON.stringify(credentials)
      )}`;
    },

    connectionStatus() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        return {
          color: "success",
          icon: "mdi-wifi",
          text: "Connected",
        };
      }
      return {
        color: "error",
        icon: "mdi-wifi-off",
        text: "Disconnected",
      };
    },

    characterCount() {
      return this.scriptText.length;
    },

    wordCount() {
      const trimmed = this.scriptText.trim();
      if (trimmed === "") return 0;
      return trimmed.split(/\s+/).length;
    },

    teleprompterParticipants() {
      return this.participants.filter(p => p.role === 'teleprompter');
    },
  },

  async mounted() {
    await this.initializeRoom();
    this.updateLastSyncTime();
    this.generateQRCode();

    // Initialize undo stack with current script content
    this.lastScriptValue = this.scriptText;
  },

  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  },

  methods: {
    async initializeRoom() {
      try {
        await this.connectWebSocket();
        this.showSnackbar("Connected to teleprompter server", "success");
      } catch (error) {
        console.error("Failed to initialize connection:", error);
        this.showSnackbar("Failed to connect to server", "error");
      }
    },

    exitTeleprompter() {
      this.$router.push("/");
    },

    // Undo/Redo functionality
    undoScript() {
      if (this.undoStack.length > 0) {
        this.isUndoRedoOperation = true;
        this.redoStack.push(this.scriptText);
        this.scriptText = this.undoStack.pop();
        this.debouncedSyncText();
        this.$nextTick(() => {
          this.isUndoRedoOperation = false;
        });
      } else {
      }
    },

    redoScript() {
      if (this.redoStack.length > 0) {
        this.isUndoRedoOperation = true;
        this.undoStack.push(this.scriptText);
        this.scriptText = this.redoStack.pop();
        this.debouncedSyncText();
        this.$nextTick(() => {
          this.isUndoRedoOperation = false;
        });
      } else {
      }
    },

    saveToUndoStack() {
      if (
        !this.isUndoRedoOperation &&
        this.scriptText !== this.lastScriptValue
      ) {
        this.undoStack.push(this.lastScriptValue);
        // Limit undo stack size
        if (this.undoStack.length > 50) {
          this.undoStack.shift();
        }
        // Clear redo stack on new changes
        this.redoStack = [];
        this.lastScriptValue = this.scriptText;
      }
    },

    handleKeyboardShortcuts(event) {
      // Ctrl+Z for undo
      if (event.ctrlKey && event.key === "z" && !event.shiftKey) {
        event.preventDefault();
        this.undoScript();
      }
      // Ctrl+Y or Ctrl+Shift+Z for redo
      else if (
        event.ctrlKey &&
        (event.key === "y" || (event.key === "z" && event.shiftKey))
      ) {
        event.preventDefault();
        this.redoScript();
      }
      // Ctrl+S for sync (save)
      else if (event.ctrlKey && event.key === "s") {
        event.preventDefault();
        this.syncScript();
      }
      // Space for play/pause (when not in input)
      else if (event.key === " " && event.target.tagName !== "TEXTAREA") {
        event.preventDefault();
        this.togglePlayback();
      }
    },

    async connectWebSocket() {
      const wsUrl = config.getWebSocketUrl();
      const wsFullUrl = `${wsUrl}/api/ws`;

      this.ws = new WebSocket(wsFullUrl);

      this.ws.onopen = () => {
        console.log("WebSocket connected");
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.showSnackbar("Connection error", "error");
      };

      this.ws.onclose = () => {
        console.log("WebSocket disconnected");
        this.showSnackbar("Disconnected from server", "warning");
      };
    },

    handleWebSocketMessage(message) {
      switch (message.type) {
        case "welcome":
          // Store our participant ID and send mode
          this.participantId = message.participant_id;
          console.log("Assigned participant ID:", this.participantId);
          this.sendMessage({ type: "mode", mode: "controller" });
          break;
        case "connection_update":
          // Update participants from server
          if (message.participants) {
            this.participants = message.participants;
            this.initializePrompterSettings();
          }
          // Auto-sync script when new participant joins (increased count)
          if (message.connection_count > this.lastConnectionCount) {
            setTimeout(() => {
              this.syncText();
              this.syncAllSettings();
            }, 1000); // Small delay to ensure connection is ready
          }
          this.lastConnectionCount = message.connection_count || 0;
          break;
        case "participants_update":
          this.participants = message.participants || [];
          this.initializePrompterSettings();
          // Sync text and settings when new teleprompter joins
          setTimeout(() => {
            this.syncText();
            this.syncAllSettings();
          }, 500);
          break;
        case "participants_list":
          this.participants = message.participants || [];
          this.initializePrompterSettings();
          break;
        case "participant_joined":
          if (
            message.participant &&
            !this.participants.find((p) => p.id === message.participant.id)
          ) {
            this.participants.push(message.participant);
            this.initializePrompterSettings();
            // Auto-sync script when new participant joins
            setTimeout(() => {
              this.syncText();
              this.syncAllSettings();
            }, 1000);
          }
          break;
        case "participant_left":
          this.participants = message.participants || this.participants.filter(
            (p) => p.id !== message.participant_id
          );
          // Clean up settings for the disconnected participant
          if (message.participant_id) {
            delete this.prompterSettings[message.participant_id];
            delete this.expandedPrompters[message.participant_id];
          }
          break;
        default:
          console.log("Received message:", message);
      }
    },

    initializePrompterSettings() {
      // Initialize settings for any new teleprompter participants
      this.teleprompterParticipants.forEach((participant) => {
        if (!this.prompterSettings[participant.id]) {
          this.prompterSettings[participant.id] = {
            scrollSpeed: this.scrollSpeed,
            textWidth: this.textWidth,
            fontSize: this.fontSize,
            horizontalMirror: this.horizontalMirror,
            verticalMirror: this.verticalMirror,
            linesPerStep: this.linesPerStep,
          };
        }
      });
    },

    syncAllSettings() {
      // Send current settings to all teleprompter participants
      this.teleprompterParticipants.forEach((participant) => {
        const settings = this.prompterSettings[participant.id];
        if (settings) {
          this.sendPrompterSettings(participant.id, settings);
        }
      });
    },

    sendMessage(message) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      }
    },

    // Playback control methods
    togglePlayback() {
      this.isPlaying = !this.isPlaying;
      this.sendMessage({
        type: this.isPlaying ? "start" : "pause",
      });
    },

    resetScrolling() {
      this.currentScrollPosition = 0;
      this.isPlaying = false;
      this.sendMessage({ type: "reset" });
    },

    goToBeginning() {
      this.currentScrollPosition = 0;
      this.sendMessage({ type: "go_to_beginning" });
    },

    goToEnd() {
      this.sendMessage({ type: "go_to_end" });
    },

    handleBackwardClick() {
      this.scrollBackLines();
    },

    handleForwardClick() {
      this.scrollForwardLines();
    },

    scrollBackLines() {
      this.sendMessage({
        type: "scroll_lines",
        direction: "backward",
        lines: this.linesPerStep,
        smooth: true,
      });
    },

    scrollForwardLines() {
      this.sendMessage({
        type: "scroll_lines",
        direction: "forward",
        lines: this.linesPerStep,
        smooth: true,
      });
    },

    // Speed and formatting controls
    adjustSpeed(delta) {
      this.scrollSpeed = Math.max(0.1, Math.min(5.0, this.scrollSpeed + delta));
      this.updateSpeed();
    },

    adjustFontSize(delta) {
      this.fontSize = Math.max(0.5, Math.min(5.0, this.fontSize + delta));
      this.updateFontSize();
    },

    adjustWidth(delta) {
      this.textWidth = Math.max(20, Math.min(100, this.textWidth + delta));
      this.updateWidth();
    },

    adjustLinesPerStep(delta) {
      this.linesPerStep = Math.max(1, Math.min(20, this.linesPerStep + delta));
    },

    updateSpeed() {
      this.sendMessage({
        type: "speed",
        value: this.scrollSpeed,
      });
    },

    updateFontSize() {
      this.sendMessage({
        type: "font_size",
        value: this.fontSize,
      });
    },

    updateWidth() {
      this.sendMessage({
        type: "width",
        value: this.textWidth,
      });
    },

    toggleHorizontalMirror() {
      this.horizontalMirror = !this.horizontalMirror;
      this.updateMirror();
    },

    toggleVerticalMirror() {
      this.verticalMirror = !this.verticalMirror;
      this.updateMirror();
    },

    updateMirror() {
      this.sendMessage({
        type: "mirror",
        horizontal: this.horizontalMirror,
        vertical: this.verticalMirror,
      });
    },

    toggleMarkdown() {
      this.markdownEnabled = !this.markdownEnabled;
      this.sendMessage({
        type: "markdown",
        enabled: this.markdownEnabled,
      });
    },

    // Per-prompter settings methods
    getPrompterSettings(participantId) {
      if (!this.prompterSettings[participantId]) {
        this.prompterSettings[participantId] = {
          scrollSpeed: this.scrollSpeed,
          textWidth: this.textWidth,
          fontSize: this.fontSize,
          horizontalMirror: this.horizontalMirror,
          verticalMirror: this.verticalMirror,
          linesPerStep: this.linesPerStep,
        };
      }
      return this.prompterSettings[participantId];
    },

    sendPrompterSettings(participantId, settings) {
      // Send all settings to the specific prompter
      this.sendMessage({
        type: "speed",
        value: settings.scrollSpeed,
        target_id: participantId,
      });
      this.sendMessage({
        type: "width",
        value: settings.textWidth,
        target_id: participantId,
      });
      this.sendMessage({
        type: "font_size",
        value: settings.fontSize,
        target_id: participantId,
      });
      this.sendMessage({
        type: "mirror",
        horizontal: settings.horizontalMirror,
        vertical: settings.verticalMirror,
        target_id: participantId,
      });
      this.sendMessage({
        type: "lines_per_step",
        value: settings.linesPerStep,
        target_id: participantId,
      });
    },

    adjustPrompterSpeed(participantId, delta) {
      const settings = this.getPrompterSettings(participantId);
      settings.scrollSpeed = Math.max(0.1, Math.min(5.0, settings.scrollSpeed + delta));
      this.sendMessage({
        type: "speed",
        value: settings.scrollSpeed,
        target_id: participantId,
      });
    },

    adjustPrompterFontSize(participantId, delta) {
      const settings = this.getPrompterSettings(participantId);
      settings.fontSize = Math.max(0.5, Math.min(5.0, settings.fontSize + delta));
      this.sendMessage({
        type: "font_size",
        value: settings.fontSize,
        target_id: participantId,
      });
    },

    adjustPrompterWidth(participantId, delta) {
      const settings = this.getPrompterSettings(participantId);
      settings.textWidth = Math.max(20, Math.min(100, settings.textWidth + delta));
      this.sendMessage({
        type: "width",
        value: settings.textWidth,
        target_id: participantId,
      });
    },

    adjustPrompterLinesPerStep(participantId, delta) {
      const settings = this.getPrompterSettings(participantId);
      settings.linesPerStep = Math.max(1, Math.min(20, settings.linesPerStep + delta));
      this.sendMessage({
        type: "lines_per_step",
        value: settings.linesPerStep,
        target_id: participantId,
      });
    },

    togglePrompterHorizontalMirror(participantId) {
      const settings = this.getPrompterSettings(participantId);
      settings.horizontalMirror = !settings.horizontalMirror;
      this.sendMessage({
        type: "mirror",
        horizontal: settings.horizontalMirror,
        vertical: settings.verticalMirror,
        target_id: participantId,
      });
    },

    togglePrompterVerticalMirror(participantId) {
      const settings = this.getPrompterSettings(participantId);
      settings.verticalMirror = !settings.verticalMirror;
      this.sendMessage({
        type: "mirror",
        horizontal: settings.horizontalMirror,
        vertical: settings.verticalMirror,
        target_id: participantId,
      });
    },

    togglePrompterExpanded(participantId) {
      this.expandedPrompters[participantId] = !this.expandedPrompters[participantId];
    },

    isPrompterExpanded(participantId) {
      return !!this.expandedPrompters[participantId];
    },

    getPrompterIndex(participantId) {
      const index = this.teleprompterParticipants.findIndex(p => p.id === participantId);
      return index + 1;
    },

    // Script management
    debouncedSyncText() {
      if (!this.isUndoRedoOperation) {
        this.saveToUndoStack();
      }

      if (this.syncTimeout) {
        clearTimeout(this.syncTimeout);
      }

      this.syncTimeout = setTimeout(() => {
        this.syncText();
      }, 500);
    },

    syncText() {
      this.sendMessage({
        type: "text",
        content: this.scriptText,
      });
      this.updateLastSyncTime();
    },

    syncScript() {
      this.syncText();
    },

    // Utility methods
    updateLastSyncTime() {
      const now = new Date();
      this.lastSyncTime = now.toLocaleTimeString();
    },

    async generateQRCode() {
      try {
        this.qrCodeDataUrl = await QRCode.toDataURL(this.joinUrl);
      } catch (error) {
        console.error("Error generating QR code:", error);
      }
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString();
    },

    disconnect() {
      if (this.ws) {
        this.ws.close();
      }
      this.$router.push("/");
    },

    showSnackbar(text, color = "success") {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },
  },
};
</script>

<style scoped>
/* Header */
.v-app-bar {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Script Editor Section */
.script-editor-section {
  background: rgba(33, 33, 33, 0.6);
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

.script-editor-container {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.script-textarea {
  height: 100%;
}

.script-textarea :deep(.v-input__control),
.script-textarea :deep(.v-field),
.script-textarea :deep(.v-field__field),
.script-textarea :deep(.v-field__input) {
  height: 100% !important;
  max-height: none !important;
}

.script-textarea :deep(.v-field__input) {
  font-family: "JetBrains Mono", "SF Mono", "Monaco", "Cascadia Code",
    "Roboto Mono", monospace !important;
  font-size: 1.1rem !important;
  line-height: 1.8 !important;
  color: #e0e0e0 !important;
  overflow-y: auto !important;
  min-height: 100% !important;
}

.script-status-bar {
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  min-height: 40px;
}

/* Sidebar */
.sidebar {
  background: rgba(48, 48, 48, 0.9);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  min-height: calc(100vh - 72px);
}

.controls-sidebar {
  height: 100%;
  overflow-y: hidden;
}

/* Control Sections */
.control-section {
  margin-bottom: 2rem;
}

.control-group {
  margin-bottom: 1rem;
}

/* Playback Controls */
.control-btn,
.play-btn {
  transition: all 0.3s ease !important;
  border-radius: 50% !important;
}

.control-btn:hover,
.play-btn:hover {
  transform: scale(1.1);
}

.play-btn {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

/* Value Displays */
.speed-display,
.lines-display,
.value-display {
  min-width: 60px;
  text-align: center;
  font-weight: 500;
  font-size: 0.875rem;
}

/* Number input text fields */
.text-center :deep(.v-field__input) {
  text-align: center;
  font-weight: 500;
}

.text-center :deep(input) {
  text-align: center;
}

/* Participants Container */
.participants-container {
  min-height: 120px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.2);
}

.participants-list {
  padding: 4px;
}

.participant-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background-color 0.2s ease;
}

.participant-item:last-child {
  border-bottom: none;
}

.participant-item:hover {
  background-color: rgba(255, 255, 255, 0.03);
}

.participant-item-you {
  background-color: rgba(0, 128, 128, 0.1);
}

.participant-item-you:hover {
  background-color: rgba(0, 128, 128, 0.15);
}

.participant-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.87);
  margin-bottom: 2px;
}

.participant-you-badge {
  color: rgb(var(--v-theme-teal));
  font-weight: 600;
  font-size: 0.8125rem;
}

.participant-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Prompter Card Styles */
.prompter-list {
  padding: 0;
}

.prompter-card {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: background-color 0.2s ease;
}

.prompter-card:last-child {
  border-bottom: none;
}

.prompter-header {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.prompter-header:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.prompter-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.87);
}

.prompter-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.prompter-settings {
  background-color: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.prompter-settings .control-group {
  margin-bottom: 0.75rem;
}

.prompter-settings .control-group:last-child {
  margin-bottom: 0;
}

/* Responsive Design */
@media (max-width: 1263px) {
  .sidebar {
    position: fixed;
    right: 0;
    top: 72px;
    z-index: 1000;
    width: 350px;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  }

  .sidebar.show {
    transform: translateX(0);
  }

  .script-editor-section {
    margin-right: 0;
  }
}

@media (max-width: 960px) {
  .script-editor-section {
    padding: 1rem;
  }

  .controls-sidebar {
    padding: 1rem;
  }

  .control-btn,
  .play-btn {
    margin: 0 0.25rem;
  }
}

/* Animation keyframes */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.script-editor-section,
.controls-sidebar {
  animation: fadeInUp 0.5s ease-out;
}
</style>
