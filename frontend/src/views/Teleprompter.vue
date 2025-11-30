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
          <div
            v-if="markdownEnabled"
            class="teleprompter-content markdown-content"
            :style="{ transform: contentMirrorTransform }"
            v-html="cachedRenderedContent"
          ></div>
          <div v-else class="teleprompter-content" :style="{ transform: contentMirrorTransform }">
            {{ teleprompterContent || defaultMessage }}
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
import { marked } from "marked";
import DOMPurify from "dompurify";

export default {
  name: "Teleprompter",

  data() {
    return {
      ws: null,
      participantId: null,  // Unique ID for this teleprompter instance
      teleprompterContent: "",
      cachedRenderedContent: "",
      defaultMessage: "Waiting for text from controller...",
      isScrolling: false,
      scrollPosition: 0,
      scrollSpeed: 1.0,
      animationId: null,
      fontSize: 2.5,
      textWidth: 100,
      horizontalMirror: false,
      linesPerStep: 5,
      isFullscreen: false,
      markdownEnabled: false,
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },
    };
  },

  computed: {
    teleprompterTransform() {
      let transforms = [
        `translateX(-50%)`,
        `translateY(${this.scrollPosition}px)`,
      ];

      return transforms.join(" ");
    },
    
    contentMirrorTransform() {
      if (this.horizontalMirror) {
        return "scaleX(-1)";
      }
      return "none";
    },
  },

  watch: {
    teleprompterContent: {
      handler(newContent) {
        if (this.markdownEnabled) {
          this.updateRenderedContent(newContent);
        }
      },
      immediate: true,
    },
    markdownEnabled: {
      handler(enabled) {
        if (enabled) {
          this.updateRenderedContent(this.teleprompterContent);
        } else {
          this.cachedRenderedContent = "";
        }
      },
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
        case "welcome":
          // Store our participant ID and send mode
          this.participantId = message.participant_id;
          console.log("Assigned participant ID:", this.participantId);
          this.sendMessage({ type: "mode", mode: "teleprompter" });
          break;
        case "text":
          this.teleprompterContent = message.content;
          this.resetScrolling();
          break;
        case "start":
          this.startScrolling();
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
          break;
        case "markdown":
          this.markdownEnabled = message.enabled;
          break;
        case "lines_per_step":
          this.linesPerStep = message.value;
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
        const scrollLimit = -(textHeight + buffer);

        if (this.scrollPosition < scrollLimit) {
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
        const targetPosition = -textHeight;

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

    updateRenderedContent(content) {
      if (!content) {
        this.cachedRenderedContent = this.defaultMessage;
        return;
      }
      try {
        const rawHtml = marked(content);
        this.cachedRenderedContent = DOMPurify.sanitize(rawHtml);
      } catch (error) {
        console.error("Error parsing markdown:", error);
        // Sanitize fallback content to prevent XSS
        this.cachedRenderedContent = DOMPurify.sanitize(content);
      }
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

/* Markdown content styles */
.markdown-content {
  white-space: normal;
  text-align: left;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 0.5em;
  margin-bottom: 0.3em;
  font-weight: bold;
  line-height: 1.4;
}

.markdown-content :deep(h1) {
  font-size: 1.5em;
}

.markdown-content :deep(h2) {
  font-size: 1.3em;
}

.markdown-content :deep(h3) {
  font-size: 1.1em;
}

.markdown-content :deep(p) {
  margin-bottom: 0.8em;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin-left: 1.5em;
  margin-bottom: 0.8em;
}

.markdown-content :deep(li) {
  margin-bottom: 0.3em;
}

.markdown-content :deep(strong) {
  font-weight: bold;
}

.markdown-content :deep(em) {
  font-style: italic;
}

.markdown-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-family: monospace;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid rgba(255, 255, 255, 0.5);
  padding-left: 1em;
  margin-left: 0;
  margin-bottom: 0.8em;
  font-style: italic;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  margin: 1em 0;
}
</style>
