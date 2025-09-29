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
            <div class="controls-sidebar pa-6">
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

                <!-- Speed Controls Row -->
                <div class="d-flex gap-3 mb-4">
                  <!-- Playback Speed -->
                  <div class="control-group flex-grow-1">
                    <label
                      class="text-caption text-medium-emphasis mb-1 d-block"
                      >Playback Speed</label
                    >
                    <div class="d-flex align-center gap-2">
                      <v-btn
                        icon="mdi-minus"
                        size="small"
                        variant="outlined"
                        @click="adjustSpeed(-0.1)"
                      />
                      <v-text-field
                        :model-value="scrollSpeed.toFixed(1) + 'x'"
                        readonly
                        variant="solo-filled"
                        hide-details
                        density="compact"
                        class="text-center"
                      />
                      <v-btn
                        icon="mdi-plus"
                        size="small"
                        variant="outlined"
                        @click="adjustSpeed(0.1)"
                      />
                    </div>
                  </div>

                  <!-- Lines to Scroll -->
                  <div class="control-group flex-grow-1">
                    <label
                      class="text-caption text-medium-emphasis mb-1 d-block"
                      >Lines to scroll</label
                    >
                    <div class="d-flex align-center gap-2">
                      <v-btn
                        icon="mdi-minus"
                        size="small"
                        variant="outlined"
                        @click="adjustLinesPerStep(-1)"
                      />
                      <v-text-field
                        :model-value="linesPerStep"
                        readonly
                        variant="solo-filled"
                        hide-details
                        density="compact"
                        class="text-center"
                      />
                      <v-btn
                        icon="mdi-plus"
                        size="small"
                        variant="outlined"
                        @click="adjustLinesPerStep(1)"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Text Settings Section -->
              <div class="control-section mb-8">
                <h3 class="text-h6 font-weight-bold mb-6">Text Settings</h3>

                <!-- Text Formatting Row -->
                <div class="d-flex gap-3 mb-4">
                  <!-- Text Width -->
                  <div class="control-group flex-grow-1">
                    <label
                      class="text-caption text-medium-emphasis mb-1 d-block"
                      >Text Width</label
                    >
                    <div class="d-flex align-center gap-2">
                      <v-btn
                        icon="mdi-minus"
                        size="small"
                        variant="outlined"
                        @click="adjustWidth(-5)"
                      />
                      <v-text-field
                        :model-value="textWidth + '%'"
                        readonly
                        variant="solo-filled"
                        hide-details
                        density="compact"
                        class="text-center"
                      />
                      <v-btn
                        icon="mdi-plus"
                        size="small"
                        variant="outlined"
                        @click="adjustWidth(5)"
                      />
                    </div>
                  </div>

                  <!-- Font Size -->
                  <div class="control-group flex-grow-1">
                    <label
                      class="text-caption text-medium-emphasis mb-1 d-block"
                      >Font Size</label
                    >
                    <div class="d-flex align-center gap-2">
                      <v-btn
                        icon="mdi-minus"
                        size="small"
                        variant="outlined"
                        @click="adjustFontSize(-0.1)"
                      />
                      <v-text-field
                        :model-value="fontSize.toFixed(1) + 'em'"
                        readonly
                        variant="solo-filled"
                        hide-details
                        density="compact"
                        class="text-center"
                      />
                      <v-btn
                        icon="mdi-plus"
                        size="small"
                        variant="outlined"
                        @click="adjustFontSize(0.1)"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Mirroring Section -->
              <div class="control-section mb-8">
                <h3 class="text-h6 font-weight-bold mb-6">Mirroring</h3>
                <div class="d-flex gap-2">
                  <v-btn
                    :color="verticalMirror ? 'teal' : 'grey-darken-2'"
                    :variant="verticalMirror ? 'flat' : 'outlined'"
                    size="small"
                    class="flex-grow-1 mr-2 ml-2"
                    @click="toggleVerticalMirror"
                  >
                    Vertical
                  </v-btn>
                  <v-btn
                    :color="horizontalMirror ? 'teal' : 'grey-darken-2'"
                    :variant="horizontalMirror ? 'flat' : 'outlined'"
                    size="small"
                    class="flex-grow-1 mr-2 ml-2"
                    @click="toggleHorizontalMirror"
                  >
                    Horizontal
                  </v-btn>
                </div>
              </div>

              <!-- Room Participants Section -->
              <div class="control-section">
                <h3 class="text-h6 font-weight-bold mb-6">Room Participants</h3>
                <div class="participants-container">
                  <div
                    v-if="participants.length === 0"
                    class="text-center text-medium-emphasis pa-6"
                  >
                    <v-icon size="48" class="mb-3 text-grey-darken-1"
                      >mdi-account-group</v-icon
                    >
                    <div class="text-body-2 mb-1">
                      No participants connected
                    </div>
                    <div class="text-caption">
                      Waiting for devices to join...
                    </div>
                  </div>

                  <div v-else class="participants-list">
                    <div
                      v-for="participant in participants"
                      :key="participant.id"
                      class="participant-card"
                      :class="{
                        'participant-card-you':
                          participant.id === participantId,
                        'participant-card-expanded': expandedParticipants.has(participant.id)
                      }"
                    >
                      <div class="participant-header" @click="toggleParticipantExpansion(participant.id)">
                        <v-icon
                          :color="
                            participant.role === 'controller' ? 'blue' : 'green'
                          "
                          size="20"
                          class="mr-3"
                        >
                          {{
                            participant.role === "controller"
                              ? "mdi-laptop"
                              : "mdi-monitor"
                          }}
                        </v-icon>

                        <div class="flex-grow-1">
                          <div class="participant-name">
                            {{
                              participant.role === "controller"
                                ? "Controller"
                                : "Teleprompter"
                            }}
                            <span
                              v-if="participant.id === participantId"
                              class="participant-you-badge"
                            >
                              (You)
                            </span>
                          </div>
                          <div class="participant-time">
                            Joined {{ formatTime(participant.joined_at) }}
                          </div>
                        </div>

                        <div class="participant-status">
                          <v-icon size="16" color="success"> mdi-circle </v-icon>
                          <!-- Show settings icon for teleprompter participants only -->
                          <v-icon 
                            v-if="participant.role === 'teleprompter'"
                            size="18" 
                            class="ml-2 participant-settings-icon"
                            :class="{ 'participant-settings-icon-expanded': expandedParticipants.has(participant.id) }"
                          > 
                            mdi-chevron-down 
                          </v-icon>
                        </div>
                      </div>

                      <!-- Per-participant settings panel (only for teleprompters) -->
                      <div 
                        v-if="participant.role === 'teleprompter' && expandedParticipants.has(participant.id)"
                        class="participant-settings-panel"
                      >
                        <div class="settings-grid">
                          <!-- Playback Speed -->
                          <div class="setting-item">
                            <label class="setting-label">Speed</label>
                            <div class="setting-control">
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-minus"
                                @click="adjustParticipantSetting(participant.id, 'scrollSpeed', -0.1)"
                                class="setting-btn"
                              ></v-btn>
                              <span class="setting-value">{{ getParticipantSetting(participant.id, 'scrollSpeed').toFixed(1) }}x</span>
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-plus"
                                @click="adjustParticipantSetting(participant.id, 'scrollSpeed', 0.1)"
                                class="setting-btn"
                              ></v-btn>
                            </div>
                          </div>

                          <!-- Font Size -->
                          <div class="setting-item">
                            <label class="setting-label">Font</label>
                            <div class="setting-control">
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-minus"
                                @click="adjustParticipantSetting(participant.id, 'fontSize', -0.1)"
                                class="setting-btn"
                              ></v-btn>
                              <span class="setting-value">{{ getParticipantSetting(participant.id, 'fontSize').toFixed(1) }}em</span>
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-plus"
                                @click="adjustParticipantSetting(participant.id, 'fontSize', 0.1)"
                                class="setting-btn"
                              ></v-btn>
                            </div>
                          </div>

                          <!-- Text Width -->
                          <div class="setting-item">
                            <label class="setting-label">Width</label>
                            <div class="setting-control">
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-minus"
                                @click="adjustParticipantSetting(participant.id, 'textWidth', -5)"
                                class="setting-btn"
                              ></v-btn>
                              <span class="setting-value">{{ getParticipantSetting(participant.id, 'textWidth') }}%</span>
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-plus"
                                @click="adjustParticipantSetting(participant.id, 'textWidth', 5)"
                                class="setting-btn"
                              ></v-btn>
                            </div>
                          </div>

                          <!-- Lines Per Step -->
                          <div class="setting-item">
                            <label class="setting-label">Lines</label>
                            <div class="setting-control">
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-minus"
                                @click="adjustParticipantSetting(participant.id, 'linesPerStep', -1)"
                                class="setting-btn"
                              ></v-btn>
                              <span class="setting-value">{{ getParticipantSetting(participant.id, 'linesPerStep') }}</span>
                              <v-btn
                                size="x-small"
                                variant="outlined"
                                icon="mdi-plus"
                                @click="adjustParticipantSetting(participant.id, 'linesPerStep', 1)"
                                class="setting-btn"
                              ></v-btn>
                            </div>
                          </div>
                        </div>

                        <!-- Mirror Controls -->
                        <div class="mirror-controls">
                          <v-btn
                            size="small"
                            variant="outlined"
                            :color="getParticipantSetting(participant.id, 'verticalMirror') ? 'primary' : 'default'"
                            @click="toggleParticipantMirror(participant.id, 'vertical')"
                            class="mirror-btn"
                          >
                            <v-icon size="16">mdi-flip-vertical</v-icon>
                            <span class="ml-1">Vertical</span>
                          </v-btn>
                          <v-btn
                            size="small"
                            variant="outlined"
                            :color="getParticipantSetting(participant.id, 'horizontalMirror') ? 'primary' : 'default'"
                            @click="toggleParticipantMirror(participant.id, 'horizontal')"
                            class="mirror-btn"
                          >
                            <v-icon size="16">mdi-flip-horizontal</v-icon>
                            <span class="ml-1">Horizontal</span>
                          </v-btn>
                        </div>

                        <!-- Reset Button -->
                        <div class="reset-controls">
                          <v-btn
                            size="small"
                            variant="outlined"
                            color="warning"
                            @click="resetParticipantSettings(participant.id)"
                            prepend-icon="mdi-restore"
                          >
                            Reset to Global
                          </v-btn>
                        </div>
                      </div>
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

      // Room management UI
      showRoomInfoDialog: false,
      editableRoomName: "",
      showSecret: false,
      qrCodeDataUrl: null,

      // UI state for new design
      showDrawer: false,
      lastSyncTime: "Never",

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

      // Control settings
      scrollSpeed: 1.0,
      textWidth: 100,
      fontSize: 2.5,
      horizontalMirror: false,
      verticalMirror: false,
      linesPerStep: 5,

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
      
      // Per-participant settings
      participantSettings: {}, // participant_id -> settings object
      expandedParticipants: new Set(), // Track which participant cards are expanded
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
        // Send mode information to backend
        this.sendMessage({ type: "mode", mode: "controller" });
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
        case "connection_update":
          // Handle real participants list from backend
          if (message.participants) {
            this.participants = message.participants;
          } else {
            // Fallback to mock participants for compatibility
            this.updateParticipantsList(message.connection_count || 0);
          }
          // Auto-sync script when new participant joins (increased count)
          if (message.connection_count > this.lastConnectionCount) {
            setTimeout(() => {
              this.syncText();
            }, 1000); // Small delay to ensure connection is ready
          }
          this.lastConnectionCount = message.connection_count || 0;
          break;
        case "participants_list":
          this.participants = message.participants || [];
          break;
        case "participant_joined":
          if (
            message.participant &&
            !this.participants.find((p) => p.id === message.participant.id)
          ) {
            this.participants.push(message.participant);
            // Auto-sync script when new participant joins
            setTimeout(() => {
              this.syncText();
            }, 1000);
          }
          break;
        case "participant_left":
          this.participants = this.participants.filter(
            (p) => p.id !== message.participant_id
          );
          break;
        default:
          console.log("Received message:", message);
      }
    },

    updateParticipantsList(connectionCount) {
      // Create mock participants based on connection count for demo purposes
      this.participants = [];
      for (let i = 0; i < connectionCount; i++) {
        this.participants.push({
          id: `participant_${i}`,
          role: i === 0 ? "controller" : "teleprompter",
          joined_at: new Date().toISOString(),
        });
      }
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

    // Per-participant settings methods
    toggleParticipantExpansion(participantId) {
      if (this.expandedParticipants.has(participantId)) {
        this.expandedParticipants.delete(participantId);
      } else {
        this.expandedParticipants.add(participantId);
      }
      // Force reactivity update
      this.expandedParticipants = new Set(this.expandedParticipants);
    },

    getParticipantSetting(participantId, settingName) {
      // Return participant-specific setting or fall back to global setting
      if (this.participantSettings[participantId] && 
          this.participantSettings[participantId][settingName] !== undefined) {
        return this.participantSettings[participantId][settingName];
      }
      // Fall back to global setting
      return this[settingName];
    },

    setParticipantSetting(participantId, settingName, value) {
      // Initialize participant settings if not exists
      if (!this.participantSettings[participantId]) {
        this.participantSettings[participantId] = {};
      }
      
      // Set the specific setting
      this.participantSettings[participantId][settingName] = value;
      
      // Send targeted message to specific participant
      this.sendMessage({
        type: settingName === 'linesPerStep' ? 'lines_per_step' : this.getMessageType(settingName),
        value: settingName === 'horizontalMirror' || settingName === 'verticalMirror' ? undefined : value,
        horizontal: settingName === 'horizontalMirror' ? value : this.getParticipantSetting(participantId, 'horizontalMirror'),
        vertical: settingName === 'verticalMirror' ? value : this.getParticipantSetting(participantId, 'verticalMirror'),
        lines: settingName === 'linesPerStep' ? value : undefined,
        target_participant_id: participantId
      });
    },

    getMessageType(settingName) {
      const mapping = {
        scrollSpeed: 'speed',
        fontSize: 'font_size',
        textWidth: 'width',
        horizontalMirror: 'mirror',
        verticalMirror: 'mirror',
        linesPerStep: 'lines_per_step'
      };
      return mapping[settingName] || settingName;
    },

    adjustParticipantSetting(participantId, settingName, delta) {
      const currentValue = this.getParticipantSetting(participantId, settingName);
      let newValue = currentValue + delta;
      
      // Apply constraints
      switch (settingName) {
        case 'scrollSpeed':
          newValue = Math.max(0.1, Math.min(5.0, newValue));
          break;
        case 'fontSize':
          newValue = Math.max(0.5, Math.min(5.0, newValue));
          break;
        case 'textWidth':
          newValue = Math.max(20, Math.min(100, newValue));
          break;
        case 'linesPerStep':
          newValue = Math.max(1, Math.min(20, newValue));
          break;
      }
      
      this.setParticipantSetting(participantId, settingName, newValue);
    },

    toggleParticipantMirror(participantId, direction) {
      const settingName = direction === 'horizontal' ? 'horizontalMirror' : 'verticalMirror';
      const currentValue = this.getParticipantSetting(participantId, settingName);
      this.setParticipantSetting(participantId, settingName, !currentValue);
    },

    resetParticipantSettings(participantId) {
      // Remove all participant-specific settings (fall back to global)
      delete this.participantSettings[participantId];
      
      // Send current global settings to the participant
      const globalSettings = {
        scrollSpeed: this.scrollSpeed,
        fontSize: this.fontSize,
        textWidth: this.textWidth,
        horizontalMirror: this.horizontalMirror,
        verticalMirror: this.verticalMirror,
        linesPerStep: this.linesPerStep
      };
      
      // Send each setting individually
      for (const [settingName, value] of Object.entries(globalSettings)) {
        this.sendMessage({
          type: this.getMessageType(settingName),
          value: settingName === 'horizontalMirror' || settingName === 'verticalMirror' ? undefined : value,
          horizontal: settingName === 'horizontalMirror' ? value : globalSettings.horizontalMirror,
          vertical: settingName === 'verticalMirror' ? value : globalSettings.verticalMirror,
          lines: settingName === 'linesPerStep' ? value : undefined,
          target_participant_id: participantId
        });
      }
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
  overflow-y: auto;
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
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.2);
}

.participants-list {
  padding: 4px;
}

/* Participant Cards */
.participant-card {
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.02);
  overflow: hidden;
  transition: all 0.2s ease;
}

.participant-card:last-child {
  margin-bottom: 0;
}

.participant-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.participant-card-you {
  background: rgba(0, 128, 128, 0.1);
  border-color: rgba(0, 128, 128, 0.3);
}

.participant-card-you:hover {
  background: rgba(0, 128, 128, 0.15);
}

.participant-card-expanded {
  border-color: rgba(255, 255, 255, 0.2);
}

/* Participant Header */
.participant-header {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  user-select: none;
}

.participant-header:hover {
  background: rgba(255, 255, 255, 0.02);
}

.participant-status {
  display: flex;
  align-items: center;
}

.participant-settings-icon {
  transition: transform 0.2s ease;
  opacity: 0.7;
}

.participant-settings-icon-expanded {
  transform: rotate(180deg);
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

/* Participant Settings Panel */
.participant-settings-panel {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  margin-bottom: 16px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.setting-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.setting-btn {
  min-width: 28px !important;
  width: 28px;
  height: 28px;
  border-radius: 4px !important;
}

.setting-value {
  min-width: 45px;
  text-align: center;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

/* Mirror Controls */
.mirror-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.mirror-btn {
  flex: 1;
  height: 32px !important;
  font-size: 0.75rem !important;
}

/* Reset Controls */
.reset-controls {
  display: flex;
  justify-content: center;
}

.reset-controls .v-btn {
  font-size: 0.75rem;
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
