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
export default {
  name: 'TeleprompterApp',
  
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
    const params = new URLSearchParams(window.location.search)
    this.channelName = params.get('room') || 'default'
    
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
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.hostname
        // Use backend API port (8001) for WebSocket connection
        this.ws = new WebSocket(`${protocol}//${host}:8001/api/ws/${this.channelName}`)
        
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
          this.updateTeleprompterText(message.content)
          break
        case 'start':
          this.startTeleprompterScrolling()
          break
        case 'pause':
          this.pauseTeleprompterScrolling()
          break
        case 'reset':
          this.resetTeleprompterScrolling()
          break
        case 'fastforward':
          this.fastForwardTeleprompter()
          break
        case 'rewind':
          this.rewindTeleprompter()
          break
        case 'speed':
          this.scrollSpeed = message.value
          break
        case 'width':
          this.updateTeleprompterWidth(message.value)
          break
        case 'mirror':
          this.setTeleprompterMirror(message.horizontal, message.vertical)
          break
        case 'fontsize':
          this.fontSize = message.value
          break
      }
    },
    
    sendMessage(message) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message))
      } else {
        console.warn('WebSocket not connected')
      }
    },
    
    // Teleprompter text methods
    updateTeleprompterText(content) {
      this.teleprompterContent = content
    },
    
    // Scrolling methods
    startTeleprompterScrolling() {
      if (!this.isScrolling) {
        this.isScrolling = true
        this.animateScroll()
      }
    },
    
    pauseTeleprompterScrolling() {
      this.isScrolling = false
      if (this.animationId) {
        cancelAnimationFrame(this.animationId)
        this.animationId = null
      }
    },
    
    resetTeleprompterScrolling() {
      this.pauseTeleprompterScrolling()
      this.scrollPosition = 0
    },
    
    fastForwardTeleprompter() {
      this.scrollPosition -= this.scrollSpeed * 5
      const maxScroll = -(this.$refs.teleprompterText?.scrollHeight || 0) - window.innerHeight
      if (this.scrollPosition < maxScroll) {
        this.scrollPosition = maxScroll
      }
    },
    
    rewindTeleprompter() {
      this.scrollPosition += this.scrollSpeed * 5
      if (this.scrollPosition > 0) {
        this.scrollPosition = 0
      }
    },
    
    animateScroll() {
      if (this.isScrolling) {
        this.scrollPosition -= this.scrollSpeed
        
        // Check if we've scrolled past the end
        const maxScroll = -(this.$refs.teleprompterText?.scrollHeight || 0) - window.innerHeight
        if (this.scrollPosition < maxScroll) {
          this.pauseTeleprompterScrolling()
        } else {
          this.animationId = requestAnimationFrame(this.animateScroll)
        }
      }
    },
    
    // Display control methods
    updateTeleprompterWidth(width) {
      this.textWidth = width
      // Send back to controller for sync
      this.sendMessage({
        type: 'width',
        value: this.textWidth
      })
    },
    
    setTeleprompterMirror(horizontal, vertical) {
      this.horizontalMirror = horizontal
      this.verticalMirror = vertical
      // Send back to controller for sync
      this.sendMessage({
        type: 'mirror',
        horizontal: this.horizontalMirror,
        vertical: this.verticalMirror
      })
    },
    
    // Local control methods
    toggleMirrorMode() {
      // Cycle through mirror modes: none -> horizontal -> vertical -> both -> none
      if (!this.horizontalMirror && !this.verticalMirror) {
        this.setTeleprompterMirror(true, false)
      } else if (this.horizontalMirror && !this.verticalMirror) {
        this.setTeleprompterMirror(false, true)
      } else if (!this.horizontalMirror && this.verticalMirror) {
        this.setTeleprompterMirror(true, true)
      } else {
        this.setTeleprompterMirror(false, false)
      }
    },
    
    changeFontSize(delta) {
      this.fontSize = Math.max(1.0, Math.min(5.0, this.fontSize + delta))
      this.sendMessage({
        type: 'fontsize',
        value: this.fontSize
      })
    },
    
    changeWidth(delta) {
      this.textWidth = Math.max(20, Math.min(100, this.textWidth + delta))
      this.updateTeleprompterWidth(this.textWidth)
    },
    
    // Fullscreen methods
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
    
    exitTeleprompter() {
      // Redirect back to landing page
      window.location.href = '/'
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
  cursor: none;
}

.teleprompter-text {
  position: absolute;
  top: 50%;
  left: 50%;
  white-space: pre-wrap;
  line-height: 1.6;
  text-align: center;
  transform: translateX(-50%);
  transition: font-size 0.3s ease, max-width 0.3s ease;
}

.teleprompter-content {
  padding: 20px;
}

/* Mirror effects */
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
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  z-index: 1000;
}

.teleprompter-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.floating-controls {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.floating-controls.visible {
  opacity: 1;
  pointer-events: auto;
}

.w-100 {
  width: 100%;
}

.flex-grow-1 {
  flex-grow: 1;
}
</style>