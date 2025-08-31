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
          <!-- Script Editor -->
          <v-col cols="12" lg="8">
            <v-card elevation="4">
              <v-card-title class="text-h5">
                <v-icon class="mr-2">mdi-script-text</v-icon>
                📝 Script Editor
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
                
                <v-btn 
                  color="primary" 
                  @click="syncText"
                  class="mt-2"
                  block
                >
                  <v-icon class="mr-2">mdi-sync</v-icon>
                  🔄 Sync Text
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Controls Panel -->
          <v-col cols="12" lg="4">
            <v-card elevation="4" class="mb-4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-play-circle</v-icon>
                Playback Controls
              </v-card-title>
              
              <v-card-text>
                <v-row>
                  <v-col cols="6">
                    <v-btn 
                      color="success" 
                      @click="startScrolling"
                      block
                      size="large"
                    >
                      <v-icon>mdi-play</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">Start</div>
                  </v-col>
                  <v-col cols="6">
                    <v-btn 
                      color="warning" 
                      @click="pauseScrolling"
                      block
                      size="large"
                    >
                      <v-icon>mdi-pause</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">Pause</div>
                  </v-col>
                  <v-col cols="6">
                    <v-btn 
                      color="info" 
                      @click="resetScrolling"
                      block
                      size="large"
                    >
                      <v-icon>mdi-skip-backward</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">Reset</div>
                  </v-col>
                  <v-col cols="6">
                    <v-btn 
                      color="secondary" 
                      @click="fastForwardText"
                      block
                      size="large"
                    >
                      <v-icon>mdi-fast-forward</v-icon>
                    </v-btn>
                    <div class="text-center text-caption mt-1">Fast Forward</div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Speed Control -->
            <v-card elevation="4" class="mb-4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-speedometer</v-icon>
                Speed Control
              </v-card-title>
              
              <v-card-text>
                <v-slider
                  v-model="scrollSpeed"
                  min="1"
                  max="10"
                  step="1"
                  thumb-label
                  @update:model-value="updateSpeed"
                  color="primary"
                />
                <div class="text-center">
                  Speed: {{ scrollSpeed }}
                </div>
              </v-card-text>
            </v-card>

            <!-- Display Controls -->
            <v-card elevation="4" class="mb-4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-format-text</v-icon>
                Display Settings
              </v-card-title>
              
              <v-card-text>
                <!-- Text Width -->
                <div class="mb-4">
                  <v-label class="mb-2">Text Width</v-label>
                  <v-row align="center">
                    <v-col cols="3">
                      <v-btn 
                        size="small" 
                        @click="decreaseWidth"
                        icon="mdi-minus"
                      />
                    </v-col>
                    <v-col cols="6" class="text-center">
                      {{ textWidth }}%
                    </v-col>
                    <v-col cols="3">
                      <v-btn 
                        size="small" 
                        @click="increaseWidth"
                        icon="mdi-plus"
                      />
                    </v-col>
                  </v-row>
                </div>

                <!-- Font Size -->
                <div class="mb-4">
                  <v-label class="mb-2">Font Size</v-label>
                  <v-row align="center">
                    <v-col cols="3">
                      <v-btn 
                        size="small" 
                        @click="decreaseFontSize"
                        icon="mdi-format-font-size-decrease"
                      />
                    </v-col>
                    <v-col cols="6" class="text-center">
                      {{ fontSize }}em
                    </v-col>
                    <v-col cols="3">
                      <v-btn 
                        size="small" 
                        @click="increaseFontSize"
                        icon="mdi-format-font-size-increase"
                      />
                    </v-col>
                  </v-row>
                </div>
              </v-card-text>
            </v-card>

            <!-- Mirror Controls -->
            <v-card elevation="4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-flip-horizontal</v-icon>
                Mirror Controls
              </v-card-title>
              
              <v-card-text>
                <v-row>
                  <v-col cols="12">
                    <v-switch
                      v-model="horizontalMirror"
                      label="Horizontal Mirror"
                      @update:model-value="updateHorizontalMirror"
                      color="primary"
                    />
                  </v-col>
                  <v-col cols="12">
                    <v-switch
                      v-model="verticalMirror"
                      label="Vertical Mirror"
                      @update:model-value="updateVerticalMirror"
                      color="primary"
                    />
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
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
  name: 'ControllerApp',
  
  data() {
    return {
      // Connection state
      ws: null,
      channelName: '',
      connectionInfo: {
        show: false,
        count: 0
      },
      
      // Script content
      scriptText: `Welcome to Remote Teleprompter!

This is your teleprompter script. Edit this text on your computer, and it will appear on your phone's screen.

Instructions:
1. Use the same channel name on all devices
2. Select "Controller Mode" on your computer
3. Select "Teleprompter Mode" on your phones/tablets
4. Click "Start" to begin scrolling

The text will scroll smoothly on the teleprompter devices. You can pause, reset, or adjust the speed as needed.

This application supports multiple teleprompter devices connected to the same channel, perfect for multi-camera setups.

Happy teleprompting! 🎬`,

      // Control settings
      scrollSpeed: 5,
      textWidth: 100,
      fontSize: 2.5,
      horizontalMirror: false,
      verticalMirror: false,
      
      // UI state
      snackbar: {
        show: false,
        text: '',
        color: 'success'
      },
      
      // Debounce timer
      syncTimeout: null
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
  },
  
  beforeUnmount() {
    if (this.ws) {
      this.ws.close()
    }
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
        this.sendMessage({ type: 'mode', mode: 'controller' })
        
        // Sync initial settings
        setTimeout(() => {
          this.syncText()
          this.updateSpeed()
          this.updateHorizontalMirror()
          this.updateVerticalMirror()
          this.updateFontSize()
          this.updateWidth()
        }, 500)
        
        // Request connection info
        setTimeout(() => {
          this.sendMessage({ type: 'request_connection_info' })
        }, 1000)
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
        this.connectionInfo.show = false
      }
    },
    
    handleMessage(message) {
      switch (message.type) {
        case 'connection_update':
          this.connectionInfo.count = message.connection_count
          this.connectionInfo.show = true
          break
          
        case 'mirror':
          // Update mirror toggles when teleprompter changes mirror mode
          this.horizontalMirror = message.horizontal
          this.verticalMirror = message.vertical
          break
          
        case 'width':
          // Update width when teleprompter changes width
          this.textWidth = message.value
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
    
    // Text synchronization
    syncText() {
      this.sendMessage({
        type: 'text',
        content: this.scriptText
      })
    },
    
    debouncedSyncText() {
      clearTimeout(this.syncTimeout)
      this.syncTimeout = setTimeout(() => {
        this.syncText()
      }, 300)
    },
    
    // Playback controls
    startScrolling() {
      this.sendMessage({ type: 'start' })
    },
    
    pauseScrolling() {
      this.sendMessage({ type: 'pause' })
    },
    
    resetScrolling() {
      this.sendMessage({ type: 'reset' })
    },
    
    fastForwardText() {
      this.sendMessage({ type: 'fastforward' })
    },
    
    // Speed control
    updateSpeed() {
      this.sendMessage({
        type: 'speed',
        value: this.scrollSpeed
      })
    },
    
    // Text width controls
    decreaseWidth() {
      this.textWidth = Math.max(20, this.textWidth - 10)
      this.updateWidth()
    },
    
    increaseWidth() {
      this.textWidth = Math.min(100, this.textWidth + 10)
      this.updateWidth()
    },
    
    updateWidth() {
      this.sendMessage({
        type: 'width',
        value: this.textWidth
      })
    },
    
    // Font size controls
    decreaseFontSize() {
      this.fontSize = Math.max(1.0, this.fontSize - 0.2)
      this.updateFontSize()
    },
    
    increaseFontSize() {
      this.fontSize = Math.min(5.0, this.fontSize + 0.2)
      this.updateFontSize()
    },
    
    updateFontSize() {
      this.sendMessage({
        type: 'fontsize',
        value: this.fontSize
      })
    },
    
    // Mirror controls
    updateHorizontalMirror() {
      this.sendMessage({
        type: 'mirror',
        horizontal: this.horizontalMirror,
        vertical: this.verticalMirror
      })
    },
    
    updateVerticalMirror() {
      this.sendMessage({
        type: 'mirror',
        horizontal: this.horizontalMirror,
        vertical: this.verticalMirror
      })
    },
    
    // Utility methods
    disconnect() {
      if (this.ws) {
        this.ws.close()
      }
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
.v-textarea :deep(.v-field__input) {
  font-family: 'Roboto Mono', monospace;
  line-height: 1.6;
}

.v-label {
  font-weight: 500;
  font-size: 0.875rem;
  opacity: 0.87;
}
</style>