<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>
        Admin - {{ roomCredentials?.room_name || "Loading..." }}
      </v-toolbar-title>
      <v-spacer />

      <!-- Participant Management Dropdown -->
      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn icon="mdi-account-group" v-bind="props" class="mr-2">
            <v-badge :content="participants.length" color="secondary" overlap>
              <v-icon>mdi-account-group</v-icon>
            </v-badge>
          </v-btn>
        </template>

        <v-card min-width="300">
          <v-card-title class="text-h6 pa-4">
            <v-icon class="mr-2">mdi-account-group</v-icon>
            Room Participants
          </v-card-title>

          <v-divider />

          <!-- Participants List -->
          <v-list>
            <v-list-item
              v-for="participant in participants"
              :key="participant.id"
              :class="{ 'bg-primary': participant.id === participantId }"
            >
              <template v-slot:prepend>
                <v-avatar
                  size="small"
                  :color="
                    participant.role === 'controller' ? 'primary' : 'secondary'
                  "
                >
                  <v-icon>{{
                    participant.role === "controller"
                      ? "mdi-laptop"
                      : "mdi-cellphone"
                  }}</v-icon>
                </v-avatar>
              </template>

              <v-list-item-title>
                {{
                  participant.role === "controller"
                    ? "💻 Controller"
                    : "📱 Teleprompter"
                }}
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
                Joined {{ formatTime(participant.joined_at) }}
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
          <v-btn
            prepend-icon="mdi-information"
            variant="tonal"
            color="info"
            size="large"
            class="ml-4 mr-4 mt-4 mb-2"
            width="calc(100% - 32px)"
            @click="showRoomInfoDialog = true"
          >
            Room Info
          </v-btn>
          <v-btn
            prepend-icon="mdi-logout"
            color="error"
            variant="tonal"
            size="large"
            class="ml-4 mr-4 mb-4 mt-2"
            width="calc(100% - 32px)"
            @click="disconnect"
          >
            Leave Room
          </v-btn>
        </v-card>
      </v-menu>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <v-row>
          <!-- Left Side - Navigation Controls -->
          <v-col cols="12" lg="3">
            <!-- Navigation Controls -->
            <v-card elevation="4" class="mb-4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-navigation-variant</v-icon>
                Navigation Controls
              </v-card-title>

              <v-card-text>
                <v-row>
                  <!-- Scroll back -->
                  <v-col cols="6">
                    <v-btn
                      color="secondary"
                      @click="scrollBackLines"
                      block
                      size="large"
                    >
                      <v-icon>mdi-arrow-up</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">Scroll Back</div>
                  </v-col>
                  <!-- Scroll forward -->
                  <v-col cols="6">
                    <v-btn
                      color="secondary"
                      @click="scrollForwardLines"
                      block
                      size="large"
                    >
                      <v-icon>mdi-arrow-down</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">
                      Scroll Forward
                    </div>
                  </v-col>
                </v-row>

                <!-- Lines to scroll control -->
                <v-text-field
                  v-model.number="scrollLines"
                  label="Lines to Scroll"
                  type="number"
                  :min="1"
                  :max="20"
                  variant="outlined"
                  class="mt-4"
                  density="compact"
                >
                  <template v-slot:prepend-inner>
                    <v-btn
                      icon="mdi-minus"
                      size="x-small"
                      variant="text"
                      @click="scrollLines = Math.max(1, scrollLines - 1)"
                    />
                  </template>
                  <template v-slot:append-inner>
                    <v-btn
                      icon="mdi-plus"
                      size="x-small"
                      variant="text"
                      @click="scrollLines = Math.min(20, scrollLines + 1)"
                    />
                  </template>
                </v-text-field>


                <v-row>
                  <!-- Go to beginning -->
                  <v-col cols="6">
                    <v-btn
                      color="primary"
                      @click="goToBeginning"
                      block
                      size="large"
                    >
                      <v-icon>mdi-skip-previous</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">Go to Start</div>
                  </v-col>
                  <!-- Go to end -->
                  <v-col cols="6">
                    <v-btn color="primary" @click="goToEnd" block size="large">
                      <v-icon>mdi-skip-next</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">Go to End</div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>


          </v-col>

          <!-- Script Editor -->
          <v-col cols="12" lg="6">
            <v-card elevation="4">
              <v-card-title class="text-h5">
                <v-icon class="mr-2">mdi-script-text</v-icon>
                Script Editor
              </v-card-title>

              <v-card-text>
                <v-textarea
                  v-model="scriptText"
                  label="Script Content"
                  placeholder="Paste or type your script here..."
                  rows="20"
                  variant="outlined"
                  auto-grow
                  @input="debouncedSyncText"
                />
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Controls Panel -->
          <v-col cols="12" lg="3">
            <!-- Playback Controls -->
            <v-card elevation="4" class="mb-4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-play-circle</v-icon>
                Playback Controls
              </v-card-title>

              <v-card-text>
                <v-row>
                  <!-- Play/Pause Toggle Button (Full Width) -->
                  <v-col cols="12">
                    <v-btn
                      :color="isPlaying ? 'warning' : 'success'"
                      @click="togglePlayback"
                      block
                      size="large"
                    >
                      <v-icon>{{
                        isPlaying ? "mdi-pause" : "mdi-play"
                      }}</v-icon>
                      <span class="ml-2">{{
                        isPlaying ? "Pause" : "Start"
                      }}</span>
                    </v-btn>
                  </v-col>
                </v-row>

                <!-- Speed Control -->
                <v-text-field
                  v-model.number="scrollSpeed"
                  label="Speed"
                  type="number"
                  :min="0.1"
                  :max="10"
                  :step="0.1"
                  variant="outlined"
                  class="mt-4"
                  density="compact"
                  @input="updateSpeed"
                >
                  <template v-slot:prepend-inner>
                    <v-btn
                      icon="mdi-minus"
                      size="x-small"
                      variant="text"
                      @click="
                        scrollSpeed = Math.max(
                          0.1,
                          Math.round((scrollSpeed - 0.1) * 10) / 10
                        );
                        updateSpeed();
                      "
                    />
                  </template>
                  <template v-slot:append-inner>
                    <v-btn
                      icon="mdi-plus"
                      size="x-small"
                      variant="text"
                      @click="
                        scrollSpeed = Math.min(
                          10,
                          Math.round((scrollSpeed + 0.1) * 10) / 10
                        );
                        updateSpeed();
                      "
                    />
                  </template>
                </v-text-field>

                <!-- Sync Text Button -->
                <v-btn color="primary" @click="syncText" class="mt-3" block>
                  <v-icon class="mr-2">mdi-sync</v-icon>
                  🔄 Sync Text
                </v-btn>
              </v-card-text>
            </v-card>

            <!-- Text & Mirror Settings -->
            <v-card elevation="4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-format-font</v-icon>
                Text & Mirror Settings
              </v-card-title>

              <v-card-text>
                <!-- Text Width -->
                <v-text-field
                  v-model.number="textWidth"
                  label="Text Width (%)"
                  type="number"
                  :min="20"
                  :max="100"
                  variant="outlined"
                  class="mb-3"
                  density="compact"
                  @input="updateWidth"
                >
                  <template v-slot:prepend-inner>
                    <v-btn
                      icon="mdi-minus"
                      size="x-small"
                      variant="text"
                      @click="
                        textWidth = Math.max(20, textWidth - 5);
                        updateWidth();
                      "
                    />
                  </template>
                  <template v-slot:append-inner>
                    <v-btn
                      icon="mdi-plus"
                      size="x-small"
                      variant="text"
                      @click="
                        textWidth = Math.min(100, textWidth + 5);
                        updateWidth();
                      "
                    />
                  </template>
                </v-text-field>

                <!-- Font Size -->
                <v-text-field
                  v-model.number="fontSize"
                  label="Font Size (em)"
                  type="number"
                  :min="0.5"
                  :max="5"
                  :step="0.1"
                  variant="outlined"
                  class="mb-3"
                  density="compact"
                  @input="updateFontSize"
                >
                  <template v-slot:prepend-inner>
                    <v-btn
                      icon="mdi-minus"
                      size="x-small"
                      variant="text"
                      @click="
                        fontSize = Math.max(
                          0.5,
                          Math.round((fontSize - 0.1) * 10) / 10
                        );
                        updateFontSize();
                      "
                    />
                  </template>
                  <template v-slot:append-inner>
                    <v-btn
                      icon="mdi-plus"
                      size="x-small"
                      variant="text"
                      @click="
                        fontSize = Math.min(
                          5,
                          Math.round((fontSize + 0.1) * 10) / 10
                        );
                        updateFontSize();
                      "
                    />
                  </template>
                </v-text-field>

                <!-- Mirror Settings -->
                <div class="mb-3">
                  <v-label class="mb-2">
                    <v-icon class="mr-1">mdi-flip-horizontal</v-icon>
                    Mirror Settings
                  </v-label>
                  <v-row>
                    <v-col cols="6">
                      <v-btn
                        :color="horizontalMirror ? 'primary' : 'secondary'"
                        @click="toggleHorizontalMirror"
                        block
                        size="small"
                        variant="outlined"
                      >
                        <v-icon class="mr-1">mdi-flip-horizontal</v-icon>
                        Horizontal
                      </v-btn>
                    </v-col>
                    <v-col cols="6">
                      <v-btn
                        :color="verticalMirror ? 'primary' : 'secondary'"
                        @click="toggleVerticalMirror"
                        block
                        size="small"
                        variant="outlined"
                      >
                        <v-icon class="mr-1">mdi-flip-vertical</v-icon>
                        Vertical
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

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
                @click="
                  copyToClipboard(roomCredentials?.room_id, 'Room ID copied!')
                "
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
                @click="
                  copyToClipboard(
                    roomCredentials?.room_secret,
                    'Room secret copied!'
                  )
                "
              />
            </template>
          </v-text-field>

          <!-- Copy Credentials Button -->
          <div class="text-center mb-4">
            <v-btn
              prepend-icon="mdi-content-copy"
              variant="outlined"
              @click="copyCredentials"
            >
              Copy All Credentials
            </v-btn>
          </div>

          <v-divider class="mb-4" />

          <!-- QR Code -->
          <div class="text-center mb-4">
            <div v-if="qrCodeDataUrl">
              <img
                :src="qrCodeDataUrl"
                alt="QR Code"
                style="max-width: 200px; border-radius: 8px"
              />
            </div>
            <div v-else>
              <v-icon size="64" color="grey">mdi-qrcode</v-icon>
            </div>
          </div>

          <!-- Join URL -->
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
      scrollLines: 5,
      currentScrollPosition: 0, // Track current scroll position in lines

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
    // Get channel name from URL params
    this.channelName = this.$route.query.room || "default";

    // Initialize room authentication
    await this.initializeRoomAuth();

    // Connect to WebSocket
    if (this.roomCredentials) {
      this.connect();
    } else {
      this.showSnackbar(
        "No room credentials found. Please create or join a room.",
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
    async initializeRoomAuth() {
      try {
        // Get room credentials from session storage
        const credentialsStr = sessionStorage.getItem("room_credentials");
        if (!credentialsStr) {
          return false;
        }

        this.roomCredentials = JSON.parse(credentialsStr);

        // Verify this is a controller role
        if (this.roomCredentials.role !== "controller") {
          this.showSnackbar(
            "Access denied: Not authorized as controller",
            "error"
          );
          return false;
        }

        // If no participant_id, we need to join the room first
        if (!this.roomCredentials.participant_id) {
          const joinData = await this.joinRoomAsController();
          if (!joinData) {
            return false;
          }
          this.roomCredentials.participant_id = joinData.participant_id;
          // Update session storage
          sessionStorage.setItem(
            "room_credentials",
            JSON.stringify(this.roomCredentials)
          );
        }

        this.participantId = this.roomCredentials.participant_id;
        this.editableRoomName = this.roomCredentials.room_name || "";
        return true;
      } catch (error) {
        console.error("Error initializing room auth:", error);
        this.showSnackbar("Failed to initialize room authentication", "error");
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
        if (!this.roomCredentials || !this.participantId) {
          throw new Error("Missing room credentials or participant ID");
        }

        // Use new WebSocket format with room_id and participant_id
        const wsUrl = config.getWebSocketUrl();
        this.ws = new WebSocket(
          `${wsUrl}/api/ws/${this.roomCredentials.room_id}/${this.participantId}`
        );

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

        // Request connection info
        setTimeout(() => {
          this.sendMessage({ type: "request_connection_info" });
        }, 1000);
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
        lines: this.scrollLines,
      });
      this.showSnackbar(`Scrolled back ${this.scrollLines} lines`, "info");
    },

    scrollForwardLines() {
      this.sendMessage({
        type: "scroll_lines",
        direction: "forward",
        lines: this.scrollLines,
      });
      this.showSnackbar(`Scrolled forward ${this.scrollLines} lines`, "info");
    },



    // Text sync
    syncText() {
      this.sendMessage({
        type: "text",
        content: this.scriptText,
      });
      this.showSnackbar("Text synced to teleprompters", "success");
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
.v-textarea :deep(.v-field__input) {
  font-family: "Roboto Mono", monospace;
  line-height: 1.6;
}

.v-label {
  font-weight: 500;
  font-size: 0.875rem;
  opacity: 0.87;
}
</style>
