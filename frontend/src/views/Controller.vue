<template>
  <v-app>
    <!-- Modern Header with Status Information -->
    <v-app-bar app elevation="0" class="modern-header" height="72">
      <v-container fluid class="d-flex align-center">
        <div class="d-flex align-center">
          <v-avatar color="primary" size="40" class="mr-3">
            <v-icon color="white">mdi-television-play</v-icon>
          </v-avatar>
          <div>
            <div class="text-h6 font-weight-bold">Teleprompter Control</div>
            <div class="text-caption text-medium-emphasis">
              Room: {{ roomCredentials?.room_name || "Connecting..." }}
            </div>
          </div>
        </div>

        <v-spacer />

        <!-- Status Indicators -->
        <div class="d-flex align-center mr-4">
          <v-chip
            :color="isPlaying ? 'success' : 'grey'"
            variant="flat"
            class="mr-2"
            size="small"
          >
            <v-icon start :icon="isPlaying ? 'mdi-play' : 'mdi-pause'"></v-icon>
            {{ isPlaying ? 'Live' : 'Paused' }}
          </v-chip>
          
          <v-chip
            :color="participants.length > 1 ? 'info' : 'warning'"
            variant="flat"
            class="mr-2"
            size="small"
          >
            <v-icon start icon="mdi-devices"></v-icon>
            {{ participants.length }} Device{{ participants.length !== 1 ? 's' : '' }}
          </v-chip>

          <v-chip
            color="primary"
            variant="flat"
            size="small"
          >
            <v-icon start icon="mdi-eye"></v-icon>
            Position: {{ Math.round(currentScrollPosition) }}
          </v-chip>
        </div>

        <!-- Action Buttons -->
        <div class="d-flex align-center">
          <!-- Quick Actions -->
          <v-btn
            icon="mdi-content-save"
            variant="text"
            class="mr-1"
            @click="saveScript"
          >
            <v-icon>mdi-content-save</v-icon>
            <v-tooltip activator="parent" location="bottom">Save Script</v-tooltip>
          </v-btn>

          <v-btn
            icon="mdi-share-variant"
            variant="text"
            class="mr-1"
            @click="showRoomInfoDialog = true"
          >
            <v-icon>mdi-share-variant</v-icon>
            <v-tooltip activator="parent" location="bottom">Share Room</v-tooltip>
          </v-btn>

          <!-- Participants Menu -->
          <v-menu offset-y>
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" variant="text" class="mr-2">
                <v-badge :content="participants.length" color="secondary" overlap>
                  <v-icon>mdi-account-group</v-icon>
                </v-badge>
                <v-tooltip activator="parent" location="bottom">Manage Participants</v-tooltip>
              </v-btn>
            </template>

            <v-card min-width="320" elevation="8">
              <v-card-title class="text-h6 pa-4 bg-primary text-white">
                <v-icon class="mr-2">mdi-account-group</v-icon>
                Room Participants
              </v-card-title>

              <v-divider />

              <!-- Participants List -->
              <v-list class="pa-0">
                <v-list-item
                  v-for="participant in participants"
                  :key="participant.id"
                  :class="{ 'bg-blue-grey-lighten-5': participant.id === participantId }"
                  class="px-4"
                >
                  <template v-slot:prepend>
                    <v-avatar
                      size="36"
                      :color="participant.role === 'controller' ? 'primary' : 'success'"
                    >
                      <v-icon color="white">{{
                        participant.role === "controller" ? "mdi-laptop" : "mdi-cellphone"
                      }}</v-icon>
                    </v-avatar>
                  </template>

                  <v-list-item-title class="font-weight-medium">
                    {{ participant.role === "controller" ? "💻 Controller" : "📱 Teleprompter" }}
                    <v-chip
                      v-if="participant.id === participantId"
                      size="x-small"
                      color="primary"
                      variant="outlined"
                      class="ml-2"
                    >
                      You
                    </v-chip>
                  </v-list-item-title>

                  <v-list-item-subtitle>
                    Connected {{ formatTime(participant.joined_at) }}
                  </v-list-item-subtitle>

                  <template v-slot:append v-if="participant.id !== participantId">
                    <v-btn
                      icon="mdi-account-remove"
                      size="small"
                      color="error"
                      variant="text"
                      @click="kickParticipant(participant.id)"
                    >
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>

              <v-divider />

              <!-- Room Actions -->
              <div class="pa-4">
                <v-btn
                  prepend-icon="mdi-information"
                  variant="outlined"
                  color="info"
                  block
                  class="mb-2"
                  @click="showRoomInfoDialog = true"
                >
                  Room Information
                </v-btn>
                <v-btn
                  prepend-icon="mdi-logout"
                  color="error"
                  variant="outlined"
                  block
                  @click="disconnect"
                >
                  Leave Room
                </v-btn>
              </div>
            </v-card>
          </v-menu>

          <!-- Settings Menu -->
          <v-btn
            icon="mdi-menu"
            variant="text"
            @click="showDrawer = !showDrawer"
          >
            <v-icon>mdi-menu</v-icon>
            <v-tooltip activator="parent" location="bottom">Settings</v-tooltip>
          </v-btn>
        </div>
      </v-container>
    </v-app-bar>

    <v-main class="modern-main">
      <v-container fluid class="pa-4">
        <!-- Modern Dashboard Layout -->
        <v-row no-gutters class="fill-height">
          <!-- Full Width Script Editor -->
          <v-col cols="12" class="pr-2">
            <!-- Script Editor with Enhanced Features -->
            <v-card elevation="2" class="fill-height script-editor-card">
              <!-- Enhanced Header with Playback Controls -->
              <v-card-title class="script-header px-6 py-4">
                <div class="d-flex align-center justify-space-between w-100">
                  <div class="d-flex align-center">
                    <!-- Character/Line count only -->
                    <div class="text-caption text-medium-emphasis">
                      {{ scriptText.split('\n').length }} lines • {{ scriptText.length }} characters
                    </div>
                  </div>
                  
                  <!-- Playback Controls in Header -->
                  <div class="d-flex align-center">
                    <!-- Playback Control Buttons -->
                    <v-btn-group variant="outlined" class="mr-3">
                      <v-btn
                        color="grey-darken-1"
                        size="small"
                        @click="handleBackwardClick"
                        @dblclick="goToBeginning"
                      >
                        <v-icon>mdi-skip-previous</v-icon>
                        <v-tooltip activator="parent" location="bottom">
                          <div>Click: Back 5 lines</div>
                          <div>Double-click: Go to start</div>
                        </v-tooltip>
                      </v-btn>
                      
                      <v-btn
                        :color="isPlaying ? 'error' : 'success'"
                        size="small"
                        @click="togglePlayback"
                      >
                        <v-icon>{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
                        <v-tooltip activator="parent" location="bottom">
                          {{ isPlaying ? 'Pause (Space)' : 'Play (Space)' }}
                        </v-tooltip>
                      </v-btn>
                      
                      <v-btn
                        color="grey-darken-1"
                        size="small"
                        @click="handleForwardClick"
                        @dblclick="goToEnd"
                      >
                        <v-icon>mdi-skip-next</v-icon>
                        <v-tooltip activator="parent" location="bottom">
                          <div>Click: Forward 5 lines</div>
                          <div>Double-click: Go to end</div>
                        </v-tooltip>
                      </v-btn>
                    </v-btn-group>

                    <!-- Script Actions -->
                    <v-btn-group variant="outlined" class="mr-3">
                      <v-btn size="small" @click="undoScript">
                        <v-icon>mdi-undo</v-icon>
                        <v-tooltip activator="parent" location="bottom">Undo (Ctrl+Z)</v-tooltip>
                      </v-btn>
                      <v-btn size="small" @click="redoScript">
                        <v-icon>mdi-redo</v-icon>
                        <v-tooltip activator="parent" location="bottom">Redo (Ctrl+Y)</v-tooltip>
                      </v-btn>
                      <v-btn size="small" @click="clearScript">
                        <v-icon>mdi-delete-outline</v-icon>
                        <v-tooltip activator="parent" location="bottom">Clear Script</v-tooltip>
                      </v-btn>
                    </v-btn-group>

                    <v-btn-group variant="outlined">
                      <v-btn size="small" @click="importScript">
                        <v-icon>mdi-file-import</v-icon>
                        <v-tooltip activator="parent" location="bottom">Import File</v-tooltip>
                      </v-btn>
                      <v-btn size="small" @click="exportScript">
                        <v-icon>mdi-download</v-icon>
                        <v-tooltip activator="parent" location="bottom">Export Script</v-tooltip>
                      </v-btn>
                    </v-btn-group>
                  </div>
                </div>
              </v-card-title>

              <v-divider />

              <!-- Script Editor Content -->
              <v-card-text class="pa-0 fill-height d-flex flex-column">
                <div class="script-editor-container flex-grow-1">
                  <v-textarea
                    v-model="scriptText"
                    placeholder="Start typing your script here, or paste existing content..."
                    variant="plain"
                    class="script-textarea"
                    hide-details
                    auto-grow
                    rows="25"
                    @input="debouncedSyncText"
                    @keydown="handleKeyboardShortcuts"
                  />
                  
                  <!-- Live Preview Indicator -->
                  <div v-if="isPlaying" class="live-preview-indicator">
                    <div class="preview-line" :style="{ top: `${currentScrollPosition * 1.6}em` }"></div>
                  </div>
                </div>

                <!-- Script Status Bar -->
                <div class="script-status-bar px-4 py-2 bg-grey-lighten-4">
                  <div class="d-flex align-center justify-space-between">
                    <div class="d-flex align-center">
                      <v-chip size="x-small" color="success" variant="flat" class="mr-2">
                        <v-icon start size="small">mdi-check-circle</v-icon>
                        Synced
                      </v-chip>
                      <span class="text-caption text-medium-emphasis">
                        Last updated: {{ lastSyncTime }}
                      </span>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Position: Line {{ Math.round(currentScrollPosition) + 1 }}
                    </div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Right Drawer for Settings -->
    <v-navigation-drawer
      v-model="showDrawer"
      location="right"
      temporary
      width="350"
      class="settings-drawer"
      :scrim="true"
    >
      <v-card flat class="fill-height">
        <v-card-title class="px-4 py-3 bg-grey-darken-3 text-white">
          <div class="d-flex align-center justify-space-between w-100">
            <div class="d-flex align-center">
              <v-icon class="mr-2">mdi-tune-vertical</v-icon>
              <span class="font-weight-bold">Settings</span>
            </div>
            <v-btn
              icon="mdi-close"
              size="small"
              variant="text"
              color="white"
              @click="showDrawer = false"
            />
          </div>
        </v-card-title>

        <v-divider />

        <v-card-text class="px-4 py-4">
          <!-- Speed Control Section -->
          <div class="mb-6">
            <div class="text-subtitle-2 font-weight-medium mb-3">Playback Speed</div>
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-body-2">Speed Control</span>
              <v-chip size="small" color="primary" variant="outlined">
                {{ scrollSpeed.toFixed(1) }}x
              </v-chip>
            </div>
            <v-slider
              v-model="scrollSpeed"
              :min="0.1"
              :max="5.0"
              :step="0.1"
              track-color="grey-lighten-2"
              color="primary"
              thumb-label="always"
              class="speed-slider"
              @input="updateSpeed"
            >
              <template v-slot:prepend>
                <v-btn
                  icon="mdi-minus"
                  size="small"
                  variant="text"
                  @click="adjustSpeed(-0.1)"
                />
              </template>
              <template v-slot:append>
                <v-btn
                  icon="mdi-plus"
                  size="small"
                  variant="text"
                  @click="adjustSpeed(0.1)"
                />
              </template>
            </v-slider>

            <!-- Quick Actions -->
            <div class="d-flex justify-space-around mt-4">
              <v-btn
                size="small"
                variant="outlined"
                color="info"
                @click="goToBeginning"
              >
                <v-icon start>mdi-page-first</v-icon>
                Start
              </v-btn>
              <v-btn
                size="small"
                variant="outlined"
                color="warning"
                @click="resetScrolling"
              >
                <v-icon start>mdi-restart</v-icon>
                Reset
              </v-btn>
              <v-btn
                size="small"
                variant="outlined"
                color="info"
                @click="goToEnd"
              >
                <v-icon start>mdi-page-last</v-icon>
                End
              </v-btn>
            </div>
          </div>

          <!-- Text Formatting Section -->
          <div class="mb-6">
            <div class="text-subtitle-2 font-weight-medium mb-3">Text Formatting</div>
            
            <!-- Font Size Control -->
            <div class="mb-4">
              <div class="d-flex align-center justify-space-between mb-1">
                <span class="text-body-2">Font Size</span>
                <v-chip size="x-small" color="primary" variant="outlined">
                  {{ fontSize.toFixed(1) }}em
                </v-chip>
              </div>
              <v-slider
                v-model="fontSize"
                :min="0.5"
                :max="5.0"
                :step="0.1"
                color="primary"
                track-color="grey-lighten-2"
                @input="updateFontSize"
              >
                <template v-slot:prepend>
                  <v-btn
                    icon="mdi-format-font-size-decrease"
                    size="x-small"
                    variant="text"
                    @click="adjustFontSize(-0.1)"
                  />
                </template>
                <template v-slot:append>
                  <v-btn
                    icon="mdi-format-font-size-increase"
                    size="x-small"
                    variant="text"
                    @click="adjustFontSize(0.1)"
                  />
                </template>
              </v-slider>
            </div>

            <!-- Text Width Control -->
            <div class="mb-4">
              <div class="d-flex align-center justify-space-between mb-1">
                <span class="text-body-2">Text Width</span>
                <v-chip size="x-small" color="primary" variant="outlined">
                  {{ textWidth }}%
                </v-chip>
              </div>
              <v-slider
                v-model="textWidth"
                :min="20"
                :max="100"
                :step="5"
                color="primary"
                track-color="grey-lighten-2"
                @input="updateWidth"
              >
                <template v-slot:prepend>
                  <v-btn
                    icon="mdi-arrow-collapse-horizontal"
                    size="x-small"
                    variant="text"
                    @click="adjustWidth(-5)"
                  />
                </template>
                <template v-slot:append>
                  <v-btn
                    icon="mdi-arrow-expand-horizontal"
                    size="x-small"
                    variant="text"
                    @click="adjustWidth(5)"
                  />
                </template>
              </v-slider>
            </div>
          </div>

          <!-- Mirror Settings Section -->
          <div class="mb-6">
            <div class="text-subtitle-2 font-weight-medium mb-3">Mirror Settings</div>
            <div class="d-flex gap-2">
              <v-btn
                :color="horizontalMirror ? 'primary' : 'grey'"
                :variant="horizontalMirror ? 'flat' : 'outlined'"
                block
                size="small"
                @click="toggleHorizontalMirror"
                class="flex-1"
              >
                <v-icon start>mdi-flip-horizontal</v-icon>
                Horizontal
              </v-btn>
              <v-btn
                :color="verticalMirror ? 'primary' : 'grey'"
                :variant="verticalMirror ? 'flat' : 'outlined'"
                block
                size="small"
                @click="toggleVerticalMirror"
                class="flex-1"
              >
                <v-icon start>mdi-flip-vertical</v-icon>
                Vertical
              </v-btn>
            </div>
          </div>

          <!-- Advanced Settings -->
          <div>
            <div class="text-subtitle-2 font-weight-medium mb-3">Advanced</div>
            <v-row>
              <v-col cols="6">
                <v-btn
                  variant="outlined"
                  size="small"
                  block
                  @click="resetAllSettings"
                >
                  <v-icon start>mdi-restore</v-icon>
                  Reset
                </v-btn>
              </v-col>
              <v-col cols="6">
                <v-btn
                  variant="outlined"
                  size="small"
                  block
                  color="primary"
                  @click="saveSettings"
                >
                  <v-icon start>mdi-content-save</v-icon>
                  Save
                </v-btn>
              </v-col>
            </v-row>
          </div>
        </v-card-text>
      </v-card>
    </v-navigation-drawer>
    <!-- Room Info Dialog -->
    <v-dialog v-model="showRoomInfoDialog" max-width="600">
      <v-card>
        <v-card-title class="text-h5 pa-6 d-flex align-center">
          <v-icon class="mr-2">mdi-information</v-icon>
          Room Information
          <v-spacer />
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="showRoomInfoDialog = false"
          />
        </v-card-title>

        <v-card-text class="pa-6">
          <!-- Editable Room Name -->
          <v-text-field
            v-model="editableRoomName"
            label="Room Name"
            variant="outlined"
            class="mb-4"
            @blur="updateRoomName"
            @keypress.enter="updateRoomName"
          >
            <template v-slot:prepend-inner>
              <v-icon>mdi-tag</v-icon>
            </template>
          </v-text-field>

          <v-divider class="mb-4" />

          <!-- Room ID (Read-only) -->
          <v-text-field
            :model-value="roomCredentials?.room_id"
            label="Room ID"
            variant="outlined"
            readonly
            class="mb-4"
          >
            <template v-slot:prepend-inner>
              <v-icon>mdi-key</v-icon>
            </template>
            <template v-slot:append-inner>
              <v-btn
                icon="mdi-content-copy"
                size="small"
                variant="text"
                @click="copyToClipboard(roomCredentials?.room_id, 'Room ID copied!')"
              />
            </template>
          </v-text-field>

          <!-- Room Secret (Read-only) -->
          <v-text-field
            :model-value="roomCredentials?.room_secret"
            label="Room Secret"
            variant="outlined"
            :type="showSecret ? 'text' : 'password'"
            readonly
            class="mb-4"
          >
            <template v-slot:prepend-inner>
              <v-icon>mdi-lock</v-icon>
            </template>
            <template v-slot:append-inner>
              <v-btn
                :icon="showSecret ? 'mdi-eye-off' : 'mdi-eye'"
                size="small"
                variant="text"
                @click="showSecret = !showSecret"
                class="mr-1"
              />
              <v-btn
                icon="mdi-content-copy"
                size="small"
                variant="text"
                @click="copyToClipboard(roomCredentials?.room_secret, 'Room secret copied!')"
              />
            </template>
          </v-text-field>

          <!-- QR Code and Join URL -->
          <div v-if="qrCodeDataUrl" class="text-center mb-4">
            <img :src="qrCodeDataUrl" alt="Room QR Code" style="max-width: 200px" />
          </div>

          <v-text-field
            :model-value="joinUrl"
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

    <!-- Snackbar for Notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
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
      scrollSpeed: 2.5,
      textWidth: 100,
      fontSize: 2.5,
      horizontalMirror: false,
      verticalMirror: false,

      // Navigation settings
      isPlaying: false,
      currentScrollPosition: 0, // Track current scroll position in lines

      // Click tracking for double-tap detection
      lastClickTime: 0,
      clickTimeout: null,

      // Section navigation

      // UI state
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },

      // Debounce timer
      syncTimeout: null,

    };
  },

  computed: {
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
    // Load saved settings
    this.loadSettings();
    
    // Initialize drawer as closed
    this.showDrawer = false;
    
    // Initialize authentication
    const authSuccess = await this.initializeAuth();

    // Connect to WebSocket
    if (authSuccess) {
      this.connect();
    } else {
      this.showSnackbar(
        "No credentials found. Please select a mode.",
        "error"
      );
      this.$router.push("/");
    }
  },

  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  },

  watch: {
    joinUrl: {
      handler() {
        this.generateQRCode();
      },
      immediate: true,
    },
    showRoomInfoDialog(newVal) {
      if (newVal) {
        this.generateQRCode();
      }
    },
  },

  methods: {
    // New methods for enhanced UI functionality
    adjustSpeed(delta) {
      this.scrollSpeed = Math.max(0.1, Math.min(5.0, 
        Math.round((this.scrollSpeed + delta) * 10) / 10
      ));
      this.updateSpeed();
    },

    adjustFontSize(delta) {
      this.fontSize = Math.max(0.5, Math.min(5.0, 
        Math.round((this.fontSize + delta) * 10) / 10
      ));
      this.updateFontSize();
    },

    adjustWidth(delta) {
      this.textWidth = Math.max(20, Math.min(100, this.textWidth + delta));
      this.updateWidth();
    },

    // Script management methods
    saveScript() {
      // For now, just show confirmation. Could be extended to save to local storage or server
      this.showSnackbar("Script changes saved", "success");
      this.lastSyncTime = new Date().toLocaleTimeString();
    },

    importScript() {
      // Create file input for importing scripts
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.txt,.md';
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (e) => {
            this.scriptText = e.target.result;
            this.debouncedSyncText();
            this.showSnackbar(`Imported script from ${file.name}`, "success");
          };
          reader.readAsText(file);
        }
      };
      input.click();
    },

    exportScript() {
      // Export script as text file
      const blob = new Blob([this.scriptText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `teleprompter-script-${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      this.showSnackbar("Script exported successfully", "success");
    },

    clearScript() {
      if (confirm("Are you sure you want to clear the entire script? This action cannot be undone.")) {
        this.scriptText = "";
        this.debouncedSyncText();
        this.showSnackbar("Script cleared", "info");
      }
    },

    undoScript() {
      // Basic undo functionality - could be extended with full history
      this.showSnackbar("Undo functionality coming soon", "info");
    },

    redoScript() {
      // Basic redo functionality - could be extended with full history
      this.showSnackbar("Redo functionality coming soon", "info");
    },

    resetAllSettings() {
      if (confirm("Reset all display settings to defaults?")) {
        this.scrollSpeed = 2.5;
        this.textWidth = 100;
        this.fontSize = 2.5;
        this.horizontalMirror = false;
        this.verticalMirror = false;
        
        // Apply all settings
        this.updateSpeed();
        this.updateWidth();
        this.updateFontSize();
        this.updateMirror();
        
        this.showSnackbar("Settings reset to defaults", "success");
      }
    },

    saveSettings() {
      // Save current settings to localStorage
      const settings = {
        scrollSpeed: this.scrollSpeed,
        textWidth: this.textWidth,
        fontSize: this.fontSize,
        horizontalMirror: this.horizontalMirror,
        verticalMirror: this.verticalMirror,
      };
      localStorage.setItem('teleprompter_settings', JSON.stringify(settings));
      this.showSnackbar("Settings saved", "success");
    },

    loadSettings() {
      // Load settings from localStorage
      try {
        const settings = localStorage.getItem('teleprompter_settings');
        if (settings) {
          const parsed = JSON.parse(settings);
          this.scrollSpeed = parsed.scrollSpeed || 2.5;
          this.textWidth = parsed.textWidth || 100;
          this.fontSize = parsed.fontSize || 2.5;
          this.horizontalMirror = parsed.horizontalMirror || false;
          this.verticalMirror = parsed.verticalMirror || false;
        }
      } catch (error) {
        console.warn("Failed to load saved settings:", error);
      }
    },

    handleKeyboardShortcuts(event) {
      // Handle keyboard shortcuts in the script editor
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 's':
            event.preventDefault();
            this.saveScript();
            break;
          case 'z':
            event.preventDefault();
            this.undoScript();
            break;
          case 'y':
            event.preventDefault();
            this.redoScript();
            break;
        }
      }
      
      // Space bar for play/pause (when not in text input)
      if (event.key === ' ' && event.target.tagName !== 'TEXTAREA') {
        event.preventDefault();
        this.togglePlayback();
      }
    },

    resetScrolling() {
      this.currentScrollPosition = 0;
      this.isPlaying = false;
      
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "reset" }));
      }
      this.showSnackbar("Reset to beginning", "info");
    },

    // Existing methods with potential updates
    async initializeAuth() {
      try {
        // Get credentials from session storage
        const credentialsStr = sessionStorage.getItem("teleprompter_credentials");
        if (!credentialsStr) {
          return false;
        }

        const credentials = JSON.parse(credentialsStr);

        // Verify this is a controller role
        if (credentials.role !== "controller") {
          this.showSnackbar(
            "Access denied: Not authorized as controller",
            "error"
          );
          return false;
        }

        return true;
      } catch (error) {
        console.error("Error initializing auth:", error);
        this.showSnackbar("Failed to initialize authentication", "error");
        return false;
      }
    },

    async joinRoomAsController() {
      try {
        const response = await fetch(`${config.getApiUrl()}/api/rooms/join`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            room_id: this.roomCredentials.room_id,
            room_secret: this.roomCredentials.room_secret,
            role: "controller",
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to join room");
        }

        const joinData = await response.json();
        if (!joinData.success) {
          this.showSnackbar(joinData.message, "error");
          return null;
        }

        return joinData;
      } catch (error) {
        console.error("Error joining room as controller:", error);
        this.showSnackbar("Failed to join room as controller", "error");
        return null;
      }
    },

    connect() {
      try {
        // Use simplified WebSocket endpoint
        const wsUrl = config.getWebSocketUrl();
        this.ws = new WebSocket(`${wsUrl}/api/ws`);

        this.setupWebSocketHandlers();
      } catch (error) {
        this.showSnackbar("Failed to connect to server", "error");
        console.error("WebSocket connection error:", error);
      }
    },

    setupWebSocketHandlers() {
      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.showSnackbar("Connected to teleprompter channel", "success");

        // Send mode information
        this.sendMessage({ type: "mode", mode: "controller" });

        // Sync initial settings
        setTimeout(() => {
          this.syncText();
          this.updateSpeed();
          this.updateHorizontalMirror();
          this.updateVerticalMirror();
          this.updateFontSize();
          this.updateWidth();
        }, 500);
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error("Error parsing message:", error);
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.showSnackbar("Connection error", "error");
      };

      this.ws.onclose = () => {
        console.log("WebSocket disconnected");
        this.showSnackbar("Disconnected from server", "warning");
        this.connectionInfo.show = false;
      };
    },

    handleMessage(message) {
      switch (message.type) {
        case "connection_update":
          this.connectionInfo.count = message.connection_count;
          this.connectionInfo.show = true;
          // Update participants list if available
          if (message.participants) {
            this.participants = message.participants;
          }
          break;

        case "mirror":
          // Update mirror toggles when teleprompter changes mirror mode
          this.horizontalMirror = message.horizontal;
          this.verticalMirror = message.vertical;
          break;

        case "width":
          // Update width when teleprompter changes width setting
          this.textWidth = message.value;
          break;

        case "font_size":
          // Update font size when teleprompter changes font size
          this.fontSize = message.value;
          break;

        case "participant_joined":
          // Show notification when a new participant joins
          if (
            message.participant &&
            message.participant.id !== this.participantId
          ) {
            const role =
              message.participant.role === "controller"
                ? "Controller"
                : "Teleprompter";

            this.showSnackbar(`${role} joined the room`, "info");

            if (message.participant.role === "teleprompter") {
              if (this.isPlaying) {
                this.pauseScrolling();
              }
              setTimeout(() => {
                this.syncText();
              }, 500);
            }
          }
          break;

        case "room_name_updated":
          // Update room name when changed by controller
          if (this.roomCredentials) {
            this.roomCredentials.room_name = message.room_name;
            sessionStorage.setItem(
              "room_credentials",
              JSON.stringify(this.roomCredentials)
            );
          }
          break;

        default:
          console.log("Received message:", message);
      }
    },

    // WebSocket communication
    sendMessage(message) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      } else {
        console.warn("WebSocket not connected");
      }
    },

    // Playback controls
    togglePlayback() {
      if (this.isPlaying) {
        this.pauseScrolling();
      } else {
        this.startScrolling();
      }
    },

    startScrolling() {
      this.isPlaying = true;
      this.sendMessage({ type: "start" });
      this.showSnackbar("Teleprompter started", "success");
    },

    pauseScrolling() {
      this.isPlaying = false;
      this.sendMessage({ type: "pause" });
      this.showSnackbar("Teleprompter paused", "warning");
    },

    // Navigation controls
    goToBeginning() {
      this.sendMessage({ type: "go_to_beginning" });
      this.showSnackbar("Teleprompter moved to beginning", "info");
    },

    goToEnd() {
      this.sendMessage({ type: "go_to_end" });
      this.showSnackbar("Teleprompter moved to end", "info");
    },

    scrollBackLines() {
      this.sendMessage({
        type: "scroll_lines",
        direction: "back",
        lines: 5, // Fixed to 5 lines
        smooth: true, // Add smooth animation flag
      });
      this.showSnackbar(`Scrolled back 5 lines`, "info");
    },

    scrollForwardLines() {
      this.sendMessage({
        type: "scroll_lines",
        direction: "forward",
        lines: 5, // Fixed to 5 lines
        smooth: true, // Add smooth animation flag
      });
      this.showSnackbar(`Scrolled forward 5 lines`, "info");
    },

    // New click handlers for single/double tap functionality
    handleBackwardClick() {
      const currentTime = Date.now();
      
      // Clear any existing timeout
      if (this.clickTimeout) {
        clearTimeout(this.clickTimeout);
        this.clickTimeout = null;
      }
      
      // Check if this is a double click (within 300ms of last click)
      if (currentTime - this.lastClickTime < 300) {
        // Double click - go to beginning
        this.goToBeginning();
        this.lastClickTime = 0; // Reset to prevent triple clicks
      } else {
        // Single click - set timeout to execute if not followed by another click
        this.lastClickTime = currentTime;
        this.clickTimeout = setTimeout(() => {
          this.scrollBackLines();
          this.clickTimeout = null;
        }, 300);
      }
    },

    handleForwardClick() {
      const currentTime = Date.now();
      
      // Clear any existing timeout
      if (this.clickTimeout) {
        clearTimeout(this.clickTimeout);
        this.clickTimeout = null;
      }
      
      // Check if this is a double click (within 300ms of last click)
      if (currentTime - this.lastClickTime < 300) {
        // Double click - go to end
        this.goToEnd();
        this.lastClickTime = 0; // Reset to prevent triple clicks
      } else {
        // Single click - set timeout to execute if not followed by another click
        this.lastClickTime = currentTime;
        this.clickTimeout = setTimeout(() => {
          this.scrollForwardLines();
          this.clickTimeout = null;
        }, 300);
      }
    },



    // Text sync
    syncText() {
      this.sendMessage({
        type: "text",
        content: this.scriptText,
      });
    },

    debouncedSyncText() {
      clearTimeout(this.syncTimeout);
      this.syncTimeout = setTimeout(() => {
        this.syncText();
      }, 1000);
    },

    // Speed controls
    updateSpeed() {
      this.sendMessage({
        type: "speed",
        value: this.scrollSpeed,
      });
    },

    // Font size controls
    updateFontSize() {
      this.sendMessage({
        type: "font_size",
        value: this.fontSize,
      });
    },

    // Width controls
    updateWidth() {
      this.sendMessage({
        type: "width",
        value: this.textWidth,
      });
    },

    // Mirror controls
    toggleHorizontalMirror() {
      this.horizontalMirror = !this.horizontalMirror;
      this.updateHorizontalMirror();
    },

    toggleVerticalMirror() {
      this.verticalMirror = !this.verticalMirror;
      this.updateVerticalMirror();
    },

    updateHorizontalMirror() {
      this.sendMessage({
        type: "mirror",
        horizontal: this.horizontalMirror,
        vertical: this.verticalMirror,
      });
    },

    updateVerticalMirror() {
      this.sendMessage({
        type: "mirror",
        horizontal: this.horizontalMirror,
        vertical: this.verticalMirror,
      });
    },


    // Utility methods
    disconnect() {
      if (this.ws) {
        this.ws.close();
      }
      // Navigate back to landing page using Vue Router
      this.$router.push("/");
    },

    showSnackbar(text, color = "success") {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },

    // Room management methods
    async kickParticipant(participantId) {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        this.showSnackbar("Cannot kick participant: not connected", "error");
        return;
      }

      if (confirm("Are you sure you want to kick this participant?")) {
        this.sendMessage({
          type: "kick_participant",
          target_participant_id: participantId,
        });
        this.showSnackbar("Participant kicked", "info");
      }
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString();
    },

    async copyToClipboard(text, successMessage) {
      try {
        await navigator.clipboard.writeText(text);
        this.showSnackbar(successMessage, "success");
      } catch (error) {
        this.showSnackbar("Failed to copy to clipboard", "error");
      }
    },

    async copyCredentials() {
      if (!this.roomCredentials) return;

      const credentials = {
        room_id: this.roomCredentials.room_id,
        room_secret: this.roomCredentials.room_secret,
        room_name: this.roomCredentials.room_name || this.editableRoomName,
      };

      try {
        await navigator.clipboard.writeText(
          JSON.stringify(credentials, null, 2)
        );
        this.showSnackbar("Room credentials copied to clipboard!", "success");
      } catch (error) {
        this.showSnackbar("Failed to copy credentials", "error");
      }
    },

    async generateQRCode() {
      if (!this.joinUrl) {
        this.qrCodeDataUrl = null;
        return;
      }

      try {
        this.qrCodeDataUrl = await QRCode.toDataURL(this.joinUrl, {
          width: 200,
          margin: 2,
        });
      } catch (error) {
        console.error("Failed to generate QR code:", error);
        this.qrCodeDataUrl = null;
      }
    },

    async updateRoomName() {
      if (
        this.editableRoomName &&
        this.editableRoomName !== this.roomCredentials?.room_name
      ) {
        try {
          const apiUrl = config.getApiUrl();
          const response = await fetch(
            `${apiUrl}/api/rooms/${this.roomCredentials.room_id}/name`,
            {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                room_id: this.roomCredentials.room_id,
                room_name: this.editableRoomName,
                participant_id: this.participantId,
              }),
            }
          );

          if (!response.ok) {
            throw new Error("Failed to update room name");
          }

          // Update local credentials
          if (this.roomCredentials) {
            this.roomCredentials.room_name = this.editableRoomName;
            sessionStorage.setItem(
              "room_credentials",
              JSON.stringify(this.roomCredentials)
            );
          }

          this.showSnackbar("Room name updated successfully", "success");
        } catch (error) {
          console.error("Error updating room name:", error);
          this.showSnackbar("Failed to update room name", "error");
        }
      }
    },
  },
};
</script>

<style scoped>
/* Modern App Layout */
.modern-header {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modern-main {
  background: linear-gradient(to bottom, #f5f5f5 0%, #fafafa 100%);
  min-height: calc(100vh - 72px);
}

/* Script Editor Enhancements */
.script-editor-card {
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.script-header {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.script-editor-container {
  position: relative;
  background: #ffffff;
}

.script-textarea :deep(.v-field__input) {
  font-family: "Roboto Mono", "SF Mono", Monaco, monospace !important;
  line-height: 1.8 !important;
  font-size: 16px !important;
  padding: 20px !important;
  color: #2c3e50 !important;
}

.script-textarea :deep(.v-field__outline) {
  display: none;
}

.live-preview-indicator {
  position: absolute;
  left: 0;
  right: 0;
  pointer-events: none;
  z-index: 1;
}

.preview-line {
  position: absolute;
  left: 20px;
  right: 20px;
  height: 2px;
  background: linear-gradient(90deg, #4caf50 0%, rgba(76, 175, 80, 0.3) 100%);
  border-radius: 1px;
  box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
  transition: top 0.3s ease;
}

.script-status-bar {
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  font-size: 12px;
}

/* Control Panel Enhancements */
.control-panel-card {
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.control-header {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

/* Enhanced Control Buttons */
.control-btn {
  width: 54px !important;
  height: 54px !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12) !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.control-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.16) !important;
}

.play-pause-btn {
  width: 80px !important;
  height: 80px !important;
  border-radius: 20px !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.play-pause-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
}

/* Settings Drawer */
.settings-drawer {
  z-index: 1000;
}

.settings-drawer .v-card {
  background-color: #1e1e1e !important;
  color: white !important;
}

.settings-drawer .v-card-text {
  background-color: #1e1e1e !important;
}

/* Enhanced Sliders */
.speed-slider :deep(.v-slider-track__fill) {
  background: linear-gradient(90deg, #1976d2 0%, #42a5f5 100%);
}

.speed-slider :deep(.v-slider-thumb) {
  background: #1976d2;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Modern Chips and Badges */
.v-chip {
  font-weight: 500;
  letter-spacing: 0.025em;
}

/* Card Transitions */
.v-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Responsive Enhancements */
@media (max-width: 1264px) {
  .script-editor-card {
    margin-bottom: 16px;
  }
}

@media (max-width: 960px) {
  .modern-header {
    height: 64px;
  }
  
  .modern-main {
    min-height: calc(100vh - 64px);
  }
  
  .script-textarea :deep(.v-field__input) {
    font-size: 14px !important;
    padding: 16px !important;
  }

  .play-pause-btn {
    width: 64px !important;
    height: 64px !important;
  }

  .control-btn {
    width: 48px !important;
    height: 48px !important;
  }
}

/* Animation Enhancements */
.v-expand-transition-enter-active,
.v-expand-transition-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Focus and Accessibility */
.v-btn:focus-visible {
  outline: 2px solid #1976d2;
  outline-offset: 2px;
}

.script-textarea:focus-within {
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

/* Typography Enhancements */
.text-h6 {
  letter-spacing: 0.0125em;
}

.text-subtitle-2 {
  font-weight: 600;
  letter-spacing: 0.0094em;
}

/* Loading and State Indicators */
.v-progress-circular {
  animation: rotation 1.5s linear infinite;
}

@keyframes rotation {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Custom Scrollbar for Script Editor */
.script-textarea :deep(.v-field__input)::-webkit-scrollbar {
  width: 8px;
}

.script-textarea :deep(.v-field__input)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.script-textarea :deep(.v-field__input)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.script-textarea :deep(.v-field__input)::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
