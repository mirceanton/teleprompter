<template>
  <v-app>
    <!-- Top Control Bar (hidden in fullscreen mode) -->
    <v-app-bar 
      v-if="!isFullscreen" 
      app 
      color="primary" 
      dark 
      density="compact"
    >
      <v-toolbar-title class="text-subtitle-1">
        📱 Teleprompter - {{ channelName }}
      </v-toolbar-title>
      <v-spacer />
      <v-chip :color="connectionStatus.color" variant="outlined" size="small">
        <v-icon start size="small">{{ connectionStatus.icon }}</v-icon>
        {{ connectionStatus.text }}
      </v-chip>
    </v-app-bar>

    <!-- Floating Controls for fullscreen mode -->
    <div 
      v-if="isFullscreen" 
      class="floating-controls"
      :class="{ 'visible': showControls }"
      @click="showControls = true"
    >
      <v-card class="pa-2" elevation="8">
        <v-btn-group density="compact">
          <v-btn 
            @click="exitFullscreen"
            icon="mdi-fullscreen-exit"
            size="small"
          />
          <v-btn 
            @click="toggleMirrorMode"
            icon="mdi-flip-horizontal"
            size="small"
          />
          <v-btn 
            @click="changeFontSize(-0.2)"
            icon="mdi-format-font-size-decrease"
            size="small"
          />
          <v-btn 
            @click="changeFontSize(0.2)"
            icon="mdi-format-font-size-increase"
            size="small"
          />
          <v-btn 
            @click="changeWidth(-10)"
            icon="mdi-arrow-collapse-horizontal"
            size="small"
          />
          <v-btn 
            @click="changeWidth(10)"
            icon="mdi-arrow-expand-horizontal"
            size="small"
          />
        </v-btn-group>
      </v-card>
    </div>

    <v-main>
      <!-- Teleprompter Display -->
      <div 
        ref="teleprompterContainer"
        class="teleprompter-container"
        :class="{ 
          'fullscreen': isFullscreen,
          'horizontal-mirror': horizontalMirror,
          'vertical-mirror': verticalMirror
        }"
        @click="enterFullscreen"
        @mousemove="onMouseMove"
      >
        <!-- Mirror Indicator -->
        <div 
          v-if="horizontalMirror || verticalMirror" 
          class="mirror-indicator"
        >
          MIRROR MODE
        </div>

        <!-- Teleprompter Text -->
        <div 
          ref="teleprompterText"
          class="teleprompter-text"
          :style="{
            fontSize: fontSize + 'em',
            maxWidth: textWidth + '%',
            transform: `translateX(-50%) translateY(${scrollPosition}px)`
          }"
        >
          <div class="teleprompter-content">
            {{ teleprompterContent || 'Waiting for text from controller...' }}
          </div>
        </div>

        <!-- Non-fullscreen controls -->
        <div v-if="!isFullscreen" class="teleprompter-controls">
          <v-card class="ma-4" elevation="4">
            <v-card-text>
              <v-row align="center">
                <v-col>
                  <v-btn 
                    color="error" 
                    variant="outlined" 
                    @click="exitTeleprompter"
                    size="small"
                  >
                    <v-icon class="mr-2">mdi-close</v-icon>
                    Exit
                  </v-btn>
                </v-col>
                <v-col cols="auto">
                  <v-btn 
                    color="primary" 
                    @click="enterFullscreen"
                    size="small"
                  >
                    <v-icon class="mr-2">mdi-fullscreen</v-icon>
                    Fullscreen
                  </v-btn>
                </v-col>
              </v-row>
              
              <!-- Quick controls -->
              <v-row class="mt-2">
                <v-col>
                  <v-btn-group density="compact" class="w-100">
                    <v-btn 
                      @click="toggleMirrorMode"
                      variant="outlined"
                      class="flex-grow-1"
                    >
                      <v-icon class="mr-1">mdi-flip-horizontal</v-icon>
                      Mirror
                    </v-btn>
                    <v-btn 
                      @click="changeFontSize(-0.2)"
                      variant="outlined"
                    >
                      A-
                    </v-btn>
                    <v-btn 
                      @click="changeFontSize(0.2)"
                      variant="outlined"
                    >
                      A+
                    </v-btn>
                    <v-btn 
                      @click="changeWidth(-10)"
                      variant="outlined"
                    >
                      ◀
                    </v-btn>
                    <v-btn 
                      @click="changeWidth(10)"
                      variant="outlined"
                    >
                      ▶
                    </v-btn>
                  </v-btn-group>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </div>
      </div>
    </v-main>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script>
import { config } from '@/utils/config.js'
import { parseMarkdownSections, getCharacterPositionForLine } from '@/utils/markdown.js'

export default {
  name: 'Teleprompter',
  
  data() {
    return {
      // Connection state
      ws: null,
      channelName: '',
      
      // Teleprompter content and state
      teleprompterContent: '',
      isScrolling: false,
      scrollPosition: 0,
      scrollSpeed: 5,
      animationId: null,
      
      // Display settings
      fontSize: 2.5,
      textWidth: 100,
      horizontalMirror: false,
      verticalMirror: false,
      
      // UI state
      isFullscreen: false,
      showControls: false,
      controlsTimeout: null,
      
      snackbar: {
        show: false,
        text: '',
        color: 'success'
      }
    }
  },
  
  computed: {
    connectionStatus() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        return {
          color: 'success',
          icon: 'mdi-wifi',
          text: 'Connected'
        }
      }
      return {
        color: 'error',
        icon: 'mdi-wifi-off',
        text: 'Disconnected'
      }
    }
  },
  
  mounted() {
    // Get channel name from URL params
    this.channelName = this.$route.query.room || 'default'
    
    // Connect to WebSocket
    this.connect()
    
    // Setup fullscreen detection
    document.addEventListener('fullscreenchange', this.onFullscreenChange)
    document.addEventListener('webkitfullscreenchange', this.onFullscreenChange)
    document.addEventListener('mozfullscreenchange', this.onFullscreenChange)
    document.addEventListener('MSFullscreenChange', this.onFullscreenChange)
  },
  
  beforeUnmount() {
    if (this.ws) {
      this.ws.close()
    }
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
    }
    
    // Remove fullscreen event listeners
    document.removeEventListener('fullscreenchange', this.onFullscreenChange)
    document.removeEventListener('webkitfullscreenchange', this.onFullscreenChange)
    document.removeEventListener('mozfullscreenchange', this.onFullscreenChange)
    document.removeEventListener('MSFullscreenChange', this.onFullscreenChange)
  },
  
  methods: {
    connect() {
      try {
        // Use configurable backend URL instead of hard-coded port
        const wsUrl = config.getWebSocketUrl()
        this.ws = new WebSocket(`${wsUrl}/api/ws/${this.channelName}`)
        
        this.setupWebSocketHandlers()
      } catch (error) {
        this.showSnackbar('Failed to connect to server', 'error')
        console.error('WebSocket connection error:', error)
      }
    },
    
    setupWebSocketHandlers() {
      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.showSnackbar('Connected to teleprompter channel', 'success')
        
        // Send mode information
        this.sendMessage({ type: 'mode', mode: 'teleprompter' })
      }
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Error parsing message:', error)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.showSnackbar('Connection error', 'error')
      }
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.showSnackbar('Disconnected from server', 'warning')
      }
    },
    
    handleMessage(message) {
      switch (message.type) {
        case 'text':
          this.teleprompterContent = message.content
          this.resetScrolling()
          break
          
        case 'start':
          this.startScrolling()
          break
          
        case 'pause':
          this.pauseScrolling()
          break
          
        case 'reset':
          this.resetScrolling()
          break
          
        case 'fast_forward':
          this.fastForward()
          break
          
        case 'speed':
          this.scrollSpeed = message.value
          break
          
        case 'font_size':
          this.fontSize = message.value
          break
          
        case 'width':
          this.textWidth = message.value
          break
          
        case 'mirror':
          this.horizontalMirror = message.horizontal
          this.verticalMirror = message.vertical
          break
          
        case 'go_to_section':
          this.goToSection(message.sectionLine)
          break
          
        case 'go_to_beginning':
          this.resetScrolling()
          break
          
        case 'go_to_end':
          this.goToEnd()
          break
          
        case 'scroll_lines':
          this.scrollByLines(message.direction, message.lines)
          break
          
        default:
          console.log('Received message:', message)
      }
    },
    
    // WebSocket communication
    sendMessage(message) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message))
      } else {
        console.warn('WebSocket not connected')
      }
    },
    
    // Scrolling controls
    startScrolling() {
      this.isScrolling = true
      this.scroll()
    },
    
    pauseScrolling() {
      this.isScrolling = false
      if (this.animationId) {
        cancelAnimationFrame(this.animationId)
      }
    },
    
    resetScrolling() {
      this.isScrolling = false
      this.scrollPosition = 0
      if (this.animationId) {
        cancelAnimationFrame(this.animationId)
      }
    },
    
    fastForward() {
      if (this.$refs.teleprompterText) {
        const textHeight = this.$refs.teleprompterText.scrollHeight
        const containerHeight = this.$refs.teleprompterContainer.clientHeight
        this.scrollPosition = Math.max(this.scrollPosition - (containerHeight * 0.3), -(textHeight - containerHeight))
      }
    },
    
    scroll() {
      if (!this.isScrolling) return
      
      // Calculate scroll speed
      const speed = this.scrollSpeed * 0.5
      this.scrollPosition -= speed
      
      // Check if we've scrolled past the end
      if (this.$refs.teleprompterText) {
        const textHeight = this.$refs.teleprompterText.scrollHeight
        const containerHeight = this.$refs.teleprompterContainer.clientHeight
        
        if (this.scrollPosition < -(textHeight + containerHeight)) {
          this.resetScrolling()
          return
        }
      }
      
      this.animationId = requestAnimationFrame(this.scroll)
    },
    
    // Section navigation methods
    goToSection(sectionLine) {
      // Calculate the scroll position based on the section line
      const lines = this.teleprompterContent.split('\n')
      const lineHeight = this.calculateLineHeight()
      
      // Position to show the section heading near the center
      const containerHeight = this.$refs.teleprompterContainer ? this.$refs.teleprompterContainer.clientHeight : 400
      const targetLinePosition = sectionLine * lineHeight
      const centerOffset = containerHeight * 0.3 // Show section heading in upper third
      
      this.scrollPosition = -(targetLinePosition - centerOffset)
    },
    
    goToEnd() {
      if (this.$refs.teleprompterText) {
        const textHeight = this.$refs.teleprompterText.scrollHeight
        const containerHeight = this.$refs.teleprompterContainer.clientHeight
        this.scrollPosition = -(textHeight - containerHeight)
      }
    },
    
    scrollByLines(direction, lines) {
      const lineHeight = this.calculateLineHeight()
      const scrollAmount = lines * lineHeight
      
      if (direction === 'back') {
        this.scrollPosition += scrollAmount
      } else {
        this.scrollPosition -= scrollAmount
      }
    },
    
    calculateLineHeight() {
      // Estimate line height based on font size
      // This is an approximation - in a real implementation you might measure actual line height
      return this.fontSize * 16 * 1.8 // fontSize (em) * base font size * line-height
    },
    
    // Font size controls
    changeFontSize(delta) {
      this.fontSize = Math.max(0.5, Math.min(5, this.fontSize + delta))
      // Sync with controller
      this.sendMessage({
        type: 'font_size',
        value: this.fontSize
      })
    },
    
    // Width controls
    changeWidth(delta) {
      this.textWidth = Math.max(20, Math.min(100, this.textWidth + delta))
      // Sync with controller
      this.sendMessage({
        type: 'width',
        value: this.textWidth
      })
    },
    
    // Mirror controls
    toggleMirrorMode() {
      this.horizontalMirror = !this.horizontalMirror
      // Sync with controller
      this.sendMessage({
        type: 'mirror',
        horizontal: this.horizontalMirror,
        vertical: this.verticalMirror
      })
    },
    
    // Fullscreen controls
    enterFullscreen() {
      const element = this.$refs.teleprompterContainer
      if (element.requestFullscreen) {
        element.requestFullscreen()
      } else if (element.webkitRequestFullscreen) {
        element.webkitRequestFullscreen()
      } else if (element.mozRequestFullScreen) {
        element.mozRequestFullScreen()
      } else if (element.msRequestFullscreen) {
        element.msRequestFullscreen()
      }
    },
    
    exitFullscreen() {
      if (document.exitFullscreen) {
        document.exitFullscreen()
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen()
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen()
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen()
      }
    },
    
    onFullscreenChange() {
      this.isFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
      )
    },
    
    onMouseMove() {
      if (this.isFullscreen) {
        this.showControls = true
        clearTimeout(this.controlsTimeout)
        this.controlsTimeout = setTimeout(() => {
          this.showControls = false
        }, 3000)
      }
    },
    
    // Utility methods
    exitTeleprompter() {
      // Navigate back to landing page using Vue Router
      this.$router.push('/')
    },
    
    showSnackbar(text, color = 'success') {
      this.snackbar.text = text
      this.snackbar.color = color
      this.snackbar.show = true
    }
  }
}
</script>

<style scoped>
.teleprompter-container {
  position: relative;
  height: 100vh;
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
  transform: translateX(-50%);
  width: 100%;
  text-align: center;
  line-height: 1.8;
  font-family: 'Roboto', Arial, sans-serif;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 0 20px;
}

.teleprompter-content {
  display: inline-block;
  max-width: 100%;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
}

.horizontal-mirror .teleprompter-text {
  transform: translateX(-50%) scaleX(-1);
}

.vertical-mirror .teleprompter-text {
  transform: translateX(-50%) scaleY(-1);
}

.horizontal-mirror.vertical-mirror .teleprompter-text {
  transform: translateX(-50%) scaleX(-1) scaleY(-1);
}

.mirror-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 0, 0, 0.8);
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  z-index: 1000;
}

.floating-controls {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.floating-controls.visible {
  opacity: 1;
}

.teleprompter-controls {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 600px;
  width: auto;
}

/* Hide scrollbar */
.teleprompter-container::-webkit-scrollbar {
  display: none;
}

.teleprompter-container {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>