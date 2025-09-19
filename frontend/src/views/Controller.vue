<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>
        💻 Controller Mode - {{ channelName }}
      </v-toolbar-title>
      <v-spacer />
      <v-chip :color="connectionStatus.color" variant="outlined">
        <v-icon start>{{ connectionStatus.icon }}</v-icon>
        {{ connectionStatus.text }}
      </v-chip>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <!-- Connection Info -->
        <v-card class="mb-4" elevation="2" v-if="connectionInfo.show">
          <v-card-text>
            <v-row align="center">
              <v-col>
                <v-icon class="mr-2">mdi-account-group</v-icon>
                <strong>{{ connectionInfo.count }}</strong> clients connected
                <v-chip
                  v-if="connectionInfo.count > 1"
                  color="success"
                  size="small"
                  class="ml-2"
                >
                  📱 Multi-teleprompter setup
                </v-chip>
              </v-col>
              <v-col cols="auto">
                <v-btn
                  color="error"
                  variant="outlined"
                  @click="disconnect"
                  size="small"
                >
                  <v-icon class="mr-2">mdi-logout</v-icon>
                  Disconnect
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <v-row>
          <!-- Left Side - Navigation Controls and Table of Contents -->
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

                <!-- Section Navigation -->
                <div class="mb-3 mt-4" v-if="sections.length > 0">
                  <v-label class="mb-2">Section Navigation</v-label>
                  <v-row>
                    <v-col cols="6">
                      <v-btn
                        color="accent"
                        @click="goToPreviousSection"
                        :disabled="!canGoToPreviousSection"
                        block
                        size="large"
                      >
                        <v-icon>mdi-page-previous</v-icon>
                      </v-btn>
                      <div class="text-center text-caption mt-1">
                        Previous Section
                      </div>
                    </v-col>
                    <v-col cols="6">
                      <v-btn
                        color="accent"
                        @click="goToNextSection"
                        :disabled="!canGoToNextSection"
                        block
                        size="large"
                      >
                        <v-icon>mdi-page-next</v-icon>
                      </v-btn>
                      <div class="text-center text-caption mt-1">
                        Next Section
                      </div>
                    </v-col>
                  </v-row>
                </div>

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

            <!-- Table of Contents -->
            <v-card elevation="4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
                Table of Contents
              </v-card-title>

              <v-card-text>
                <div v-if="sections.length > 0" class="toc-list">
                  <div
                    v-for="(section, index) in sections"
                    :key="index"
                    class="toc-item"
                    :class="`toc-level-${section.level}`"
                    @click="goToSection(section)"
                  >
                    <v-btn
                      variant="text"
                      size="small"
                      class="justify-start text-left"
                      block
                    >
                      <span class="text-truncate">{{ section.title }}</span>
                    </v-btn>
                  </div>
                </div>
                <div v-else class="text-center text-disabled">
                  <v-icon class="mb-2">mdi-format-list-bulleted-square</v-icon>
                  <div class="text-caption">
                    No sections could be parsed from the script.<br />
                    Expected markdown headings (# ## ###).
                  </div>
                </div>
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

            <!-- AI Scrolling Controls -->
            <v-card elevation="4" class="mb-4">
              <v-card-title class="text-h6 d-flex align-center">
                <v-icon class="mr-2">mdi-brain</v-icon>
                AI Scrolling
                <v-spacer />
                <v-switch
                  v-model="aiScrolling.enabled"
                  :disabled="!aiScrolling.available"
                  @change="toggleAIScrolling"
                  color="primary"
                  hide-details
                  density="compact"
                />
              </v-card-title>

              <v-card-text v-if="aiScrolling.enabled">
                <!-- Audio Source Selection - Compact -->
                <v-select
                  v-model="aiScrolling.config.audio_source"
                  :items="audioSourceOptions"
                  @update:modelValue="updateAIScrollingConfig"
                  density="compact"
                  variant="outlined"
                  label="Audio Source"
                  hide-details
                  class="mb-3"
                ></v-select>

                <!-- Advanced Settings -->
                <v-expansion-panels variant="accordion">
                  <v-expansion-panel title="Advanced Settings">
                    <v-expansion-panel-text>
                      <!-- Look Ahead/Behind -->
                      <v-text-field
                        v-model.number="aiScrolling.config.look_ahead_chars"
                        label="Look Ahead (characters)"
                        type="number"
                        :min="50"
                        :max="500"
                        variant="outlined"
                        class="mb-3"
                        density="compact"
                        @input="updateAIScrollingConfig"
                      >
                        <template v-slot:prepend-inner>
                          <v-btn
                            icon="mdi-minus"
                            size="x-small"
                            variant="text"
                            @click="
                              aiScrolling.config.look_ahead_chars = Math.max(
                                50,
                                aiScrolling.config.look_ahead_chars - 10
                              );
                              updateAIScrollingConfig();
                            "
                          />
                        </template>
                        <template v-slot:append-inner>
                          <v-btn
                            icon="mdi-plus"
                            size="x-small"
                            variant="text"
                            @click="
                              aiScrolling.config.look_ahead_chars = Math.min(
                                500,
                                aiScrolling.config.look_ahead_chars + 10
                              );
                              updateAIScrollingConfig();
                            "
                          />
                        </template>
                      </v-text-field>

                      <v-text-field
                        v-model.number="aiScrolling.config.look_behind_chars"
                        label="Look Behind (characters)"
                        type="number"
                        :min="25"
                        :max="200"
                        variant="outlined"
                        class="mb-3"
                        density="compact"
                        @input="updateAIScrollingConfig"
                      >
                        <template v-slot:prepend-inner>
                          <v-btn
                            icon="mdi-minus"
                            size="x-small"
                            variant="text"
                            @click="
                              aiScrolling.config.look_behind_chars = Math.max(
                                25,
                                aiScrolling.config.look_behind_chars - 5
                              );
                              updateAIScrollingConfig();
                            "
                          />
                        </template>
                        <template v-slot:append-inner>
                          <v-btn
                            icon="mdi-plus"
                            size="x-small"
                            variant="text"
                            @click="
                              aiScrolling.config.look_behind_chars = Math.min(
                                200,
                                aiScrolling.config.look_behind_chars + 5
                              );
                              updateAIScrollingConfig();
                            "
                          />
                        </template>
                      </v-text-field>

                      <!-- Confidence Threshold -->
                      <div class="mb-3">
                        <v-label class="mb-2">Confidence Threshold</v-label>
                        <v-slider
                          v-model="aiScrolling.config.confidence_threshold"
                          :min="0.3"
                          :max="1.0"
                          :step="0.05"
                          thumb-label
                          @update:modelValue="updateAIScrollingConfig"
                        ></v-slider>
                      </div>

                      <!-- Pause Threshold -->
                      <v-text-field
                        v-model.number="
                          aiScrolling.config.pause_threshold_seconds
                        "
                        label="Pause Threshold (seconds)"
                        type="number"
                        :min="1.0"
                        :max="10.0"
                        :step="0.5"
                        variant="outlined"
                        class="mb-3"
                        density="compact"
                        @input="updateAIScrollingConfig"
                      >
                        <template v-slot:prepend-inner>
                          <v-btn
                            icon="mdi-minus"
                            size="x-small"
                            variant="text"
                            @click="
                              aiScrolling.config.pause_threshold_seconds =
                                Math.max(
                                  1.0,
                                  Math.round(
                                    (aiScrolling.config
                                      .pause_threshold_seconds -
                                      0.5) *
                                      10
                                  ) / 10
                                );
                              updateAIScrollingConfig();
                            "
                          />
                        </template>
                        <template v-slot:append-inner>
                          <v-btn
                            icon="mdi-plus"
                            size="x-small"
                            variant="text"
                            @click="
                              aiScrolling.config.pause_threshold_seconds =
                                Math.min(
                                  10.0,
                                  Math.round(
                                    (aiScrolling.config
                                      .pause_threshold_seconds +
                                      0.5) *
                                      10
                                  ) / 10
                                );
                              updateAIScrollingConfig();
                            "
                          />
                        </template>
                      </v-text-field>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

                <!-- AI Status Display - Compact -->
                <div class="mt-3">
                  <v-chip
                    :color="aiScrolling.status.color"
                    variant="tonal"
                    size="small"
                    class="mb-1"
                  >
                    <v-icon start size="small">{{
                      aiScrolling.status.icon
                    }}</v-icon>
                    {{ aiScrolling.status.text }}
                  </v-chip>
                </div>
              </v-card-text>

              <v-card-text v-else>
                <div
                  v-if="!aiScrolling.available"
                  class="text-caption text-error text-center"
                >
                  Speech recognition not available
                </div>
                <div v-else class="text-caption text-disabled text-center">
                  Enable AI Scrolling to configure options
                </div>
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
import {
  parseMarkdownSections,
  getCurrentSection,
  getNextSection,
  getPreviousSection,
  generateTableOfContents,
} from "@/utils/markdown.js";

export default {
  name: "Controller",

  data() {
    return {
      // Connection state
      ws: null,
      channelName: "",
      connectionInfo: {
        show: false,
        count: 0,
      },

      // Script content
      scriptText: `# Welcome to Remote Teleprompter!

This is your teleprompter script. Edit this text on your computer, and it will appear on your phone's screen.

## Instructions

1. Use the same channel name on all devices
2. Select "Controller Mode" on your computer
3. Select "Teleprompter Mode" on your phones/tablets
4. Click "Start" to begin scrolling

## Features

The text will scroll smoothly on the teleprompter devices. You can pause, reset, or adjust the speed as needed.

### Section Navigation

You can now navigate between sections using markdown headings! Use the Previous/Next Section buttons or click on items in the Table of Contents.

### Multi-Camera Support

This application supports multiple teleprompter devices connected to the same channel, perfect for multi-camera setups.

## Conclusion

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

      // AI Scrolling state
      aiScrolling: {
        enabled: false,
        available: false,
        config: {
          look_ahead_chars: 100,
          look_behind_chars: 50,
          confidence_threshold: 0.7,
          pause_threshold_seconds: 3.0,
          scroll_speed_multiplier: 1.0,
          audio_source: "controller",
        },
        status: {
          color: "default",
          icon: "mdi-microphone-off",
          text: "AI Scrolling Disabled",
        },
      },

      // Audio recording state
      audioRecording: {
        active: false,
        mediaRecorder: null,
        stream: null,
      },
    };
  },

  computed: {
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

    // Audio source options for AI scrolling
    audioSourceOptions() {
      return [
        { title: "Controller (This Device)", value: "controller" },
        { title: "Teleprompter Device", value: "teleprompter" },
      ];
    },

    // Parse markdown sections from script text
    sections() {
      return parseMarkdownSections(this.scriptText);
    },

    // Current section based on scroll position
    currentSection() {
      return getCurrentSection(this.sections, this.currentScrollPosition);
    },

    // Check if can navigate to previous section
    canGoToPreviousSection() {
      return (
        getPreviousSection(this.sections, this.currentScrollPosition) !== null
      );
    },

    // Check if can navigate to next section
    canGoToNextSection() {
      return getNextSection(this.sections, this.currentScrollPosition) !== null;
    },
  },

  mounted() {
    // Get channel name from URL params
    this.channelName = this.$route.query.room || "default";

    // Check AI scrolling availability
    this.checkAIScrollingAvailability();

    // Connect to WebSocket
    this.connect();
  },

  beforeUnmount() {
    // Clean up audio recording
    if (this.audioRecording.active) {
      this.stopAudioRecording();
    }

    if (this.ws) {
      this.ws.close();
    }
  },

  methods: {
    async checkAIScrollingAvailability() {
      try {
        // Check if microphone access is available
        const hasMediaDevices =
          navigator.mediaDevices && navigator.mediaDevices.getUserMedia;

        if (hasMediaDevices) {
          // Check with backend if AI scrolling is available
          const response = await fetch(
            `${config.getApiUrl()}/api/channel/${this.channelName}/ai-scrolling`
          );
          const data = await response.json();
          this.aiScrolling.available = data.available || false;
        } else {
          this.aiScrolling.available = false;
        }
      } catch (error) {
        console.warn("Could not check AI scrolling availability:", error);
        this.aiScrolling.available = false;
      }
    },

    connect() {
      try {
        // Use configurable backend URL instead of hard-coded port
        const wsUrl = config.getWebSocketUrl();
        this.ws = new WebSocket(`${wsUrl}/api/ws/${this.channelName}`);

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

        case "ai_scrolling_started":
          this.aiScrolling.status = {
            color: "success",
            icon: "mdi-microphone",
            text: "AI Scrolling Active",
          };
          this.showSnackbar("AI Scrolling started", "success");
          break;

        case "ai_scrolling_stopped":
          this.aiScrolling.status = {
            color: "default",
            icon: "mdi-microphone-off",
            text: "AI Scrolling Disabled",
          };
          this.showSnackbar("AI Scrolling stopped", "info");
          break;

        case "ai_scrolling_config_updated":
          this.aiScrolling.config = { ...message.config };
          break;

        case "ai_scrolling_error":
          this.aiScrolling.status = {
            color: "error",
            icon: "mdi-alert",
            text: `AI Error: ${message.error}`,
          };
          this.showSnackbar(`AI Scrolling Error: ${message.error}`, "error");
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

    // Section navigation controls
    goToPreviousSection() {
      const prevSection = getPreviousSection(
        this.sections,
        this.currentScrollPosition
      );
      if (prevSection) {
        this.goToSection(prevSection);
        this.showSnackbar(`Moved to: ${prevSection.title}`, "info");
      }
    },

    goToNextSection() {
      const nextSection = getNextSection(
        this.sections,
        this.currentScrollPosition
      );
      if (nextSection) {
        this.goToSection(nextSection);
        this.showSnackbar(`Moved to: ${nextSection.title}`, "info");
      }
    },

    goToSection(section) {
      this.currentScrollPosition = section.start;
      this.sendMessage({
        type: "go_to_section",
        sectionLine: section.start,
        sectionTitle: section.title,
      });
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

    // AI Scrolling methods
    async toggleAIScrolling() {
      if (this.aiScrolling.enabled) {
        await this.startAIScrolling();
      } else {
        await this.stopAIScrolling();
      }
    },

    async startAIScrolling() {
      try {
        // Check if we need to start audio recording
        if (this.aiScrolling.config.audio_source === "controller") {
          await this.startAudioRecording();
        }

        // Start AI scrolling session
        this.sendMessage({
          type: "ai_scrolling_start",
          script_content: this.scriptText,
          config: this.aiScrolling.config,
        });

        this.aiScrolling.status = {
          color: "info",
          icon: "mdi-loading",
          text: "Starting AI Scrolling...",
        };
      } catch (error) {
        console.error("Error starting AI scrolling:", error);
        // Don't disable the UI checkbox, just show error status
        this.aiScrolling.status = {
          color: "error",
          icon: "mdi-alert",
          text: `Error: ${error.message}`,
        };
        this.showSnackbar(
          `Failed to start AI scrolling: ${error.message}`,
          "error"
        );
      }
    },

    async stopAIScrolling() {
      try {
        // Stop audio recording if active
        if (this.audioRecording.active) {
          this.stopAudioRecording();
        }

        // Stop AI scrolling session
        this.sendMessage({
          type: "ai_scrolling_stop",
        });

        this.aiScrolling.status = {
          color: "default",
          icon: "mdi-microphone-off",
          text: "AI Scrolling Disabled",
        };
      } catch (error) {
        console.error("Error stopping AI scrolling:", error);
        this.showSnackbar(
          `Error stopping AI scrolling: ${error.message}`,
          "error"
        );
      }
    },

    updateAIScrollingConfig() {
      if (this.aiScrolling.enabled) {
        this.sendMessage({
          type: "ai_scrolling_config",
          ...this.aiScrolling.config,
        });
      }
    },

    async startAudioRecording() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });

        this.audioRecording.stream = stream;
        this.audioRecording.mediaRecorder = new MediaRecorder(stream, {
          mimeType: "audio/webm;codecs=opus",
        });

        this.audioRecording.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && this.aiScrolling.enabled) {
            this.sendAudioChunk(event.data);
          }
        };

        // Record in small chunks for real-time processing
        this.audioRecording.mediaRecorder.start(1000); // 1 second chunks
        this.audioRecording.active = true;
      } catch (error) {
        throw new Error(`Microphone access denied: ${error.message}`);
      }
    },

    stopAudioRecording() {
      if (this.audioRecording.mediaRecorder) {
        this.audioRecording.mediaRecorder.stop();
        this.audioRecording.mediaRecorder = null;
      }

      if (this.audioRecording.stream) {
        this.audioRecording.stream.getTracks().forEach((track) => track.stop());
        this.audioRecording.stream = null;
      }

      this.audioRecording.active = false;
    },

    async sendAudioChunk(audioBlob) {
      try {
        const arrayBuffer = await audioBlob.arrayBuffer();
        const base64Audio = btoa(
          String.fromCharCode(...new Uint8Array(arrayBuffer))
        );

        this.sendMessage({
          type: "audio_chunk",
          audio_data: base64Audio,
        });
      } catch (error) {
        console.error("Error sending audio chunk:", error);
      }
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

.toc-list {
  max-height: 300px;
  overflow-y: auto;
}

.toc-item {
  margin-bottom: 2px;
  cursor: pointer;
}

.toc-level-1 {
  margin-left: 0;
}

.toc-level-2 {
  margin-left: 16px;
}

.toc-level-3 {
  margin-left: 32px;
}

.toc-level-4 {
  margin-left: 48px;
}

.toc-level-5 {
  margin-left: 64px;
}

.toc-level-6 {
  margin-left: 80px;
}

.toc-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-radius: 4px;
}
</style>
