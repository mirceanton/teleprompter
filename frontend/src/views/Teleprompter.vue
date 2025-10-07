<template>
  <v-app>
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
      <!-- Teleprompter Display -->
      <div
        ref="teleprompterContainer"
        class="teleprompter-container"
        :class="{ fullscreen: isFullscreen }"
        @click="enterFullscreen"
      >
        <div
          ref="teleprompterText"
          class="teleprompter-text"
          :style="{
            fontSize: fontSize + 'em',
            maxWidth: textWidth + '%',
            transform: teleprompterTransform,
          }"
        >
          <div class="teleprompter-content">
            {{ teleprompterContent || "Waiting for text from controller..." }}
          </div>
        </div>

        <!-- REC Indicator Badge -->
        <div v-if="obsRecording" class="rec-indicator">
          <div class="rec-dot"></div>
          <span class="rec-text">REC</span>
        </div>

        <!-- Countdown Overlay (Default Mode) -->
        <div v-if="showCountdown && !waitingForOBS" class="countdown-overlay">
          <div class="countdown-circle">
            <div class="countdown-number">{{ Math.ceil(countdownValue) }}</div>
          </div>
          <div class="countdown-text">Starting in...</div>
          <div v-if="obsConnected && obsRecording" class="obs-status">
            <v-icon color="success" size="24">mdi-check-circle</v-icon>
            <span class="ml-2">OBS Ready</span>
          </div>
        </div>

        <!-- Waiting for OBS Overlay (Strict Mode) -->
        <div v-if="waitingForOBS" class="waiting-overlay">
          <v-progress-circular
            indeterminate
            color="teal"
            size="80"
            width="6"
            class="mb-4"
          />
          <div class="waiting-text">Waiting for recording to start...</div>
          <div v-if="waitTimeout > 0 && waitTimeout <= 5" class="timeout-warning">
            <v-icon color="warning" size="24">mdi-alert</v-icon>
            <span class="ml-2">Aborting in {{ Math.ceil(waitTimeout) }}s...</span>
          </div>
        </div>
      </div>
    </v-main>

    <v-snackbar top right v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script>
import { config } from "@/utils/config.js";

export default {
  name: "Teleprompter",

  data() {
    return {
      ws: null,
      teleprompterContent: "",
      isScrolling: false,
      scrollPosition: 0,
      scrollSpeed: 1.0,
      animationId: null,
      fontSize: 2.5,
      textWidth: 100,
      horizontalMirror: false,
      verticalMirror: false,
      isFullscreen: false,
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },
      
      // OBS Integration
      obsConnected: false,
      obsRecording: false,
      showCountdown: false,
      countdownValue: 0,
      countdownInterval: null,
      waitingForOBS: false,
      waitTimeout: 30,
      waitTimeoutInterval: null,
    };
  },

  computed: {
    teleprompterTransform() {
      let transforms = [
        `translateX(-50%)`,
        `translateY(${this.scrollPosition}px)`,
      ];

      if (this.horizontalMirror) {
        transforms.push("scaleX(-1)");
      }

      if (this.verticalMirror) {
        transforms.push("scaleY(-1)");
      }

      return transforms.join(" ");
    },
  },

  async mounted() {
    this.connect();

    document.addEventListener("fullscreenchange", this.onFullscreenChange);
    document.addEventListener(
      "webkitfullscreenchange",
      this.onFullscreenChange
    );
    document.addEventListener("mozfullscreenchange", this.onFullscreenChange);
    document.addEventListener("MSFullscreenChange", this.onFullscreenChange);
  },

  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    document.removeEventListener("fullscreenchange", this.onFullscreenChange);
    document.removeEventListener(
      "webkitfullscreenchange",
      this.onFullscreenChange
    );
    document.removeEventListener(
      "mozfullscreenchange",
      this.onFullscreenChange
    );
    document.removeEventListener("MSFullscreenChange", this.onFullscreenChange);
    
    // Clean up OBS integration timers
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
    }
    if (this.waitTimeoutInterval) {
      clearInterval(this.waitTimeoutInterval);
    }
  },

  methods: {
    exitTeleprompter() {
      this.$router.push("/");
    },

    connect() {
      try {
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
        this.sendMessage({ type: "mode", mode: "teleprompter" });
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
      };
    },

    handleMessage(message) {
      switch (message.type) {
        case "text":
          this.teleprompterContent = message.content;
          this.resetScrolling();
          break;
        case "start":
          this.handleStartMessage(message);
          break;
        case "pause":
          this.pauseScrolling();
          break;
        case "reset":
          this.resetScrolling();
          break;
        case "speed":
          this.scrollSpeed = message.value;
          break;
        case "font_size":
          this.fontSize = message.value;
          break;
        case "width":
          this.textWidth = message.value;
          break;
        case "mirror":
          this.horizontalMirror = message.horizontal;
          this.verticalMirror = message.vertical;
          break;
        case "go_to_beginning":
          this.resetScrolling();
          break;
        case "go_to_end":
          this.goToEnd();
          break;
        case "scroll_lines":
          this.scrollByLines(message.direction, message.lines, message.smooth);
          break;
        case "obs_status":
          this.handleObsStatus(message);
          break;
        case "obs_recording_confirmed":
          this.handleObsConfirmation();
          break;
      }
    },

    sendMessage(message) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      }
    },

    startScrolling() {
      this.isScrolling = true;
      this.scroll();
    },

    pauseScrolling() {
      this.isScrolling = false;
      if (this.animationId) {
        cancelAnimationFrame(this.animationId);
      }
    },

    resetScrolling() {
      this.isScrolling = false;
      if (this.animationId) {
        cancelAnimationFrame(this.animationId);
      }
      // Smoothly animate to beginning
      this.animateToPosition(0);
    },

    scroll() {
      if (!this.isScrolling) return;

      const speed = this.scrollSpeed * 0.5 * -1;
      this.scrollPosition += speed;

      if (this.$refs.teleprompterText) {
        const textHeight = this.$refs.teleprompterText.scrollHeight;
        const containerHeight = this.$refs.teleprompterContainer.clientHeight;

        // Allow scrolling from start (0) to beyond end (-textHeight) with buffer
        // Buffer allows text to scroll slightly past for a cleaner finish
        const buffer = containerHeight * 0.5;
        const scrollLimit = this.verticalMirror
          ? textHeight + buffer
          : -(textHeight + buffer);

        const isOutOfBounds = this.verticalMirror
          ? this.scrollPosition > scrollLimit
          : this.scrollPosition < scrollLimit;

        if (isOutOfBounds) {
          this.resetScrolling();
          return;
        }
      }

      this.animationId = requestAnimationFrame(this.scroll);
    },

    goToEnd() {
      if (this.$refs.teleprompterText) {
        const textHeight = this.$refs.teleprompterText.scrollHeight;

        // Position so the last line of text is centered
        // Text top is at: containerHeight/2 + scrollPosition
        // Text bottom is at: containerHeight/2 + scrollPosition + textHeight
        // We want text bottom at center: containerHeight/2
        // Therefore: scrollPosition = -textHeight
        const targetPosition = this.verticalMirror ? textHeight : -textHeight;

        // Smoothly animate to end
        this.animateToPosition(targetPosition);
      }
    },

    scrollByLines(direction, lines, smooth = false) {
      const lineHeight = this.fontSize * 16 * 1.8;
      const scrollAmount = lines * lineHeight;

      let targetPosition;
      if (direction === "backward") {
        // Scroll backward/up: increase scrollPosition (less negative)
        targetPosition = this.scrollPosition + scrollAmount;
      } else if (direction === "forward") {
        // Scroll forward/down: decrease scrollPosition (more negative)
        targetPosition = this.scrollPosition - scrollAmount;
      } else {
        console.warn(`Unknown scroll direction: ${direction}`);
        return;
      }

      if (smooth) {
        this.animateToPosition(targetPosition);
      } else {
        this.scrollPosition = targetPosition;
      }
    },

    animateToPosition(targetPosition) {
      const startPosition = this.scrollPosition;
      const distance = targetPosition - startPosition;
      const duration = 500;
      const startTime = performance.now();

      const animate = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const easeProgress =
          progress < 0.5
            ? 4 * progress * progress * progress
            : 1 - Math.pow(-2 * progress + 2, 3) / 2;

        this.scrollPosition = startPosition + distance * easeProgress;

        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };

      requestAnimationFrame(animate);
    },

    enterFullscreen() {
      const element = this.$refs.teleprompterContainer;
      if (element.requestFullscreen) {
        element.requestFullscreen();
      } else if (element.webkitRequestFullscreen) {
        element.webkitRequestFullscreen();
      } else if (element.mozRequestFullScreen) {
        element.mozRequestFullScreen();
      } else if (element.msRequestFullscreen) {
        element.msRequestFullscreen();
      }
    },

    onFullscreenChange() {
      this.isFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
      );
    },

    showSnackbar(text, color = "success") {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },

    // OBS Integration methods
    handleStartMessage(message) {
      const countdown = message.countdown || 0;
      const waitForOBS = message.waitForOBS || false;

      if (waitForOBS) {
        // Strict mode - wait for OBS confirmation
        this.waitingForOBS = true;
        this.waitTimeout = 30;
        
        // Start timeout countdown
        this.waitTimeoutInterval = setInterval(() => {
          this.waitTimeout -= 0.1;
          if (this.waitTimeout <= 0) {
            this.cancelWaitingForOBS();
            this.showSnackbar("OBS confirmation timeout - starting anyway", "warning");
          }
        }, 100);
      } else if (countdown > 0) {
        // Default mode - show countdown
        this.showCountdown = true;
        this.countdownValue = countdown;
        
        // Update countdown every 100ms for smooth animation
        this.countdownInterval = setInterval(() => {
          this.countdownValue -= 0.1;
          if (this.countdownValue <= 0) {
            this.finishCountdown();
          }
        }, 100);
      } else {
        // No countdown, start immediately
        this.startScrolling();
      }
    },

    handleObsStatus(message) {
      this.obsConnected = message.connected || false;
      this.obsRecording = message.recording || false;
    },

    handleObsConfirmation() {
      if (this.waitingForOBS) {
        this.cancelWaitingForOBS();
        this.startScrolling();
      }
    },

    finishCountdown() {
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
        this.countdownInterval = null;
      }
      this.showCountdown = false;
      this.countdownValue = 0;
      this.startScrolling();
    },

    cancelWaitingForOBS() {
      if (this.waitTimeoutInterval) {
        clearInterval(this.waitTimeoutInterval);
        this.waitTimeoutInterval = null;
      }
      this.waitingForOBS = false;
      this.waitTimeout = 30;
    },
  },
};
</script>

<style scoped>
.teleprompter-container {
  position: relative;
  height: 100%;
  background: #000;
  color: #fff;
  overflow: hidden;
  cursor: pointer;
}

.teleprompter-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
}

.teleprompter-text {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  text-align: center;
  line-height: 1.8;
  font-family: "Roboto", Arial, sans-serif;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 0 20px;
}

.teleprompter-content {
  display: inline-block;
  max-width: 100%;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
}

/* REC Indicator Badge */
.rec-indicator {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  background: #d32f2f;
  padding: 8px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.rec-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  animation: pulse 1.5s ease-in-out infinite;
}

.rec-text {
  color: #fff;
  font-weight: bold;
  font-size: 14px;
  letter-spacing: 1px;
}

/* Countdown Overlay */
.countdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  z-index: 9998;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease-in;
}

.countdown-circle {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00897b, #26a69a);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 137, 123, 0.4);
  margin-bottom: 24px;
}

.countdown-number {
  font-size: 80px;
  font-weight: bold;
  color: #fff;
}

.countdown-text {
  font-size: 24px;
  color: #fff;
  margin-top: 16px;
}

.obs-status {
  margin-top: 24px;
  display: flex;
  align-items: center;
  color: #4caf50;
  font-size: 18px;
}

/* Waiting Overlay */
.waiting-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.95);
  z-index: 9998;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease-in;
}

.waiting-text {
  font-size: 28px;
  color: #fff;
  margin-top: 24px;
}

.timeout-warning {
  margin-top: 32px;
  display: flex;
  align-items: center;
  color: #ffb300;
  font-size: 20px;
}

/* Animations */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
