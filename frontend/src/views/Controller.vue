<template>
  <v-app theme="dark">
    <!-- Header with App Title -->
    <v-app-bar app elevation="0" height="72" color="grey-darken-4">
      <v-container fluid class="d-flex align-center">
        <div class="d-flex align-center">
          <v-icon color="teal" size="32" class="mr-3"
            >mdi-presentation-play</v-icon
          >
          <div class="text-h5 font-weight-bold">Teleprompter</div>
        </div>
        <v-spacer />
      </v-container>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-0 fill-height">
        <v-row no-gutters class="fill-height">
          <!-- Left Side - Script Editor -->
          <v-col cols="12" lg="8" xl="9" class="d-flex flex-column">
            <div class="script-editor-section pa-6">
              <!-- Script Editor Header -->
              <div class="d-flex align-center justify-space-between mb-6">
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


              <!-- Script Status Footer -->
              <div
                class="script-status-footer mt-4 pa-4 rounded bg-grey-darken-3"
              >
                <div class="d-flex align-center justify-space-between">
                  <div class="d-flex align-center">
                    <v-chip
                      size="small"
                      color="success"
                      variant="flat"
                      class="mr-3"
                    >
                      <v-icon start size="small">mdi-check-circle</v-icon>
                      Synced
                    </v-chip>
                    <span class="text-caption text-medium-emphasis">
                      Last update: {{ lastSyncTime }}
                    </span>
                  </div>
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

              <!-- Script Editor Textarea -->
              <div class="script-editor-container flex-grow-1">
                <v-textarea
                  v-model="scriptText"
                  variant="outlined"
                  class="script-textarea"
                  hide-details
                  @input="debouncedSyncText"
                  @keydown="handleKeyboardShortcuts"
                />
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
                    <v-number-input
                      v-model.number="scrollSpeed"
                      label="Playback Speed"
                      variant="solo-filled"
                      control-variant="split"
                      hide-details
                      density="compact"
                      :min="0.1"
                      :max="5.0"
                      :step="0.1"
                      suffix="x"
                      @update:model-value="updateSpeed"
                    >
                      <template v-slot:display-value="{ displayValue }">
                        {{ Number(displayValue).toFixed(1) }}
                      </template>
                    </v-number-input>
                  </div>

                  <!-- Lines to Scroll -->
                  <div class="control-group flex-grow-1">
                    <v-number-input
                      v-model="linesPerStep"
                      label="Lines to scroll"
                      variant="solo-filled"
                      control-variant="split"
                      hide-details
                      density="compact"
                      :min="1"
                      :max="20"
                      :step="1"
                    />
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
                    <v-number-input
                      v-model="textWidth"
                      label="Text Width"
                      variant="solo-filled"
                      control-variant="split"
                      hide-details
                      density="compact"
                      :min="20"
                      :max="100"
                      :step="5"
                      suffix="%"
                      @update:model-value="updateWidth"
                    />
                  </div>

                  <!-- Font Size -->
                  <div class="control-group flex-grow-1">
                    <v-number-input
                      v-model.number="fontSize"
                      label="Font Size"
                      variant="solo-filled"
                      control-variant="split"
                      hide-details
                      density="compact"
                      :min="0.5"
                      :max="5.0"
                      :step="0.1"
                      suffix="em"
                      @update:model-value="updateFontSize"
                    >
                      <template v-slot:display-value="{ displayValue }">
                        {{ Number(displayValue).toFixed(1) }}
                      </template>
                    </v-number-input>
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
                <div
                  class="participants-container"
                  style="min-height: 120px; max-height: 300px; overflow-y: auto"
                >
                  <div
                    v-if="participants.length === 0"
                    class="text-center text-medium-emphasis pa-4"
                  >
                    <v-icon size="48" class="mb-2 text-grey-darken-1"
                      >mdi-account-group</v-icon
                    >
                    <div class="text-body-2">No participants connected</div>
                    <div class="text-caption">
                      Waiting for devices to join...
                    </div>
                  </div>
                  
                  <!-- Data Iterator for Participants -->
                  <v-data-iterator
                    v-else
                    :items="participants"
                    item-value="id"
                    hide-default-footer
                    class="pa-0"
                  >
                    <template v-slot:default="{ items }">
                      <v-row dense>
                        <v-col
                          v-for="participant in items"
                          :key="participant.raw.id"
                          cols="12"
                          class="pb-2"
                        >
                          <v-card
                            variant="outlined"
                            :color="participant.raw.id === participantId ? 'teal-darken-4' : 'grey-darken-3'"
                            class="participant-card"
                            density="compact"
                          >
                            <v-card-text class="pa-3">
                              <div class="d-flex align-center">
                                <v-avatar
                                  size="28"
                                  :color="
                                    participant.raw.role === 'controller'
                                      ? 'primary'
                                      : 'success'
                                  "
                                  class="mr-3"
                                >
                                  <v-icon size="16" color="white">{{
                                    participant.raw.role === "controller"
                                      ? "mdi-laptop"
                                      : "mdi-cellphone"
                                  }}</v-icon>
                                </v-avatar>
                                
                                <div class="flex-grow-1">
                                  <div class="text-body-2 font-weight-medium">
                                    {{
                                      participant.raw.role === "controller"
                                        ? "Controller"
                                        : "Teleprompter"
                                    }}
                                    <v-chip
                                      v-if="participant.raw.id === participantId"
                                      size="x-small"
                                      color="teal"
                                      variant="flat"
                                      class="ml-2"
                                    >
                                      You
                                    </v-chip>
                                  </div>
                                  <div class="text-caption text-medium-emphasis">
                                    {{ formatTime(participant.raw.joined_at) }}
                                  </div>
                                </div>
                              </div>
                            </v-card-text>
                          </v-card>
                        </v-col>
                      </v-row>
                    </template>
                  </v-data-iterator>
                </div>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Room Information Dialog -->
    <v-dialog v-model="showRoomInfoDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          <v-icon class="mr-2">mdi-information</v-icon>
          Room Information
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <v-text-field
            label="Room Name"
            v-model="editableRoomName"
            variant="outlined"
            class="mb-3"
          />

          <v-text-field
            :label="`Room ID: ${roomCredentials?.room_id || 'Loading...'}`"
            :value="roomCredentials?.room_id || 'Loading...'"
            variant="outlined"
            readonly
            class="mb-3"
          >
            <template v-slot:append-inner>
              <v-btn
                icon="mdi-content-copy"
                size="small"
                variant="text"
                @click="
                  copyToClipboard(
                    roomCredentials?.room_id || '',
                    'Room ID copied!'
                  )
                "
              />
            </template>
          </v-text-field>

          <v-text-field
            :label="`Room Secret: ${
              showSecret
                ? roomCredentials?.room_secret || 'Loading...'
                : '••••••••'
            }`"
            :value="
              showSecret
                ? roomCredentials?.room_secret || 'Loading...'
                : '••••••••'
            "
            variant="outlined"
            readonly
            class="mb-3"
          >
            <template v-slot:append-inner>
              <v-btn
                :icon="showSecret ? 'mdi-eye-off' : 'mdi-eye'"
                size="small"
                variant="text"
                @click="showSecret = !showSecret"
              />
              <v-btn
                icon="mdi-content-copy"
                size="small"
                variant="text"
                @click="
                  copyToClipboard(
                    roomCredentials?.room_secret || '',
                    'Room Secret copied!'
                  )
                "
                class="ml-1"
              />
            </template>
          </v-text-field>

          <div v-if="qrCodeDataUrl" class="text-center mb-3">
            <img :src="qrCodeDataUrl" alt="QR Code" style="max-width: 200px" />
            <div class="text-caption text-medium-emphasis mt-2">
              Scan QR code to join the teleprompter
            </div>
          </div>

          <v-text-field
            :value="joinUrl"
            label="Teleprompter Join URL"
            variant="outlined"
            readonly
          >
            <template v-slot:prepend-inner>
              <v-icon>mdi-link</v-icon>
            </template>
            <template v-slot:append-inner>
              <v-btn
                icon="mdi-content-copy"
                size="small"
                variant="text"
                @click="copyToClipboard(joinUrl, 'Join URL copied!')"
              />
            </template>
          </v-text-field>
        </v-card-text>
      </v-card>
    </v-dialog>

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
        this.showSnackbar("Connected to teleprompter channel", "success");
      } catch (error) {
        console.error("Failed to initialize connection:", error);
        this.showSnackbar("Failed to connect to server", "error");
      }
    },

    // Undo/Redo functionality
    undoScript() {
      if (this.undoStack.length > 0) {
        this.isUndoRedoOperation = true;
        this.redoStack.push(this.scriptText);
        this.scriptText = this.undoStack.pop();
        this.debouncedSyncText();
        this.showSnackbar("Undo completed", "info");
        this.$nextTick(() => {
          this.isUndoRedoOperation = false;
        });
      } else {
        this.showSnackbar("Nothing to undo", "warning");
      }
    },

    redoScript() {
      if (this.redoStack.length > 0) {
        this.isUndoRedoOperation = true;
        this.undoStack.push(this.scriptText);
        this.scriptText = this.redoStack.pop();
        this.debouncedSyncText();
        this.showSnackbar("Redo completed", "info");
        this.$nextTick(() => {
          this.isUndoRedoOperation = false;
        });
      } else {
        this.showSnackbar("Nothing to redo", "warning");
      }
    },

    saveToUndoStack() {
      if (!this.isUndoRedoOperation && this.scriptText !== this.lastScriptValue) {
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
      if (event.ctrlKey && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        this.undoScript();
      }
      // Ctrl+Y or Ctrl+Shift+Z for redo
      else if (event.ctrlKey && (event.key === 'y' || (event.key === 'z' && event.shiftKey))) {
        event.preventDefault();
        this.redoScript();
      }
      // Ctrl+S for sync (save)
      else if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        this.syncScript();
      }
      // Space for play/pause (when not in input)
      else if (event.key === ' ' && event.target.tagName !== 'TEXTAREA') {
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
        case "connection_update":
          // Simple connection count update - create mock participants
          this.updateParticipantsList(message.connection_count || 0);
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
          role: i === 0 ? 'controller' : 'teleprompter',
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
      this.showSnackbar(
        this.isPlaying ? "Teleprompter started" : "Teleprompter paused",
        "info"
      );
    },

    resetScrolling() {
      this.currentScrollPosition = 0;
      this.isPlaying = false;
      this.sendMessage({ type: "reset" });
      this.showSnackbar("Reset to beginning", "info");
    },

    goToBeginning() {
      this.currentScrollPosition = 0;
      this.sendMessage({ type: "go_to_beginning" });
      this.showSnackbar("Jumped to beginning", "info");
    },

    goToEnd() {
      this.sendMessage({ type: "go_to_end" });
      this.showSnackbar("Jumped to end", "info");
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
      this.showSnackbar(`Scrolled back ${this.linesPerStep} lines`, "info");
    },

    scrollForwardLines() {
      this.sendMessage({
        type: "scroll_lines",
        direction: "forward",
        lines: this.linesPerStep,
        smooth: true,
      });
      this.showSnackbar(`Scrolled forward ${this.linesPerStep} lines`, "info");
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
      this.showSnackbar("Script synchronized", "success");
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

    copyToClipboard(text, successMessage) {
      navigator.clipboard
        .writeText(text)
        .then(() => {
          this.showSnackbar(successMessage, "success");
        })
        .catch((err) => {
          console.error("Failed to copy: ", err);
          this.showSnackbar("Failed to copy to clipboard", "error");
        });
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString();
    },

    kickParticipant(participantId) {
      this.sendMessage({
        type: "kick_participant",
        participant_id: participantId,
      });
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

    handleKeyboardShortcuts(event) {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case "s":
            event.preventDefault();
            this.syncScript();
            break;
          case "z":
            event.preventDefault();
            this.undoScript();
            break;
          case "y":
            event.preventDefault();
            this.redoScript();
            break;
        }
      }

      if (event.key === " " && !event.target.closest(".v-textarea")) {
        event.preventDefault();
        this.togglePlayback();
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
  min-height: calc(100vh - 72px);
}

.script-textarea :deep(.v-field__input) {
  font-family: "JetBrains Mono", "SF Mono", "Monaco", "Cascadia Code",
    "Roboto Mono", monospace !important;
  font-size: 1.1rem !important;
  line-height: 1.8 !important;
  color: #e0e0e0 !important;
  height: 500px !important;
  min-height: 500px !important;
  max-height: 500px !important;
  overflow-y: auto !important;
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

/* Participants Container */
.participants-container {
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.participant-card {
  transition: all 0.2s ease;
}

.participant-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
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
