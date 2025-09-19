<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>
        💻 Controller Mode - {{ roomName || channelName }}
      </v-toolbar-title>
      <v-spacer />
      
      <!-- Participants Dropdown -->
      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn
            icon
            v-bind="props"
            v-if="roomInfo.participants && roomInfo.participants.length > 0"
          >
            <v-badge 
              :content="roomInfo.participants.length" 
              color="secondary"
              overlap
            >
              <v-icon>mdi-account-group</v-icon>
            </v-badge>
          </v-btn>
        </template>
        
        <v-card min-width="300">
          <v-card-title class="text-h6">
            <v-icon class="mr-2">mdi-account-group</v-icon>
            Room Participants
          </v-card-title>
          
          <v-card-text>
            <v-list>
              <v-list-item 
                v-for="participant in roomInfo.participants" 
                :key="participant.participant_id"
              >
                <template v-slot:prepend>
                  <v-icon :color="participant.is_controller ? 'primary' : 'secondary'">
                    {{ participant.mode === 'controller' ? 'mdi-laptop' : 'mdi-cellphone' }}
                  </v-icon>
                </template>
                
                <v-list-item-title>
                  {{ participant.mode === 'controller' ? '💻 Controller' : '📱 Teleprompter' }}
                  <v-chip 
                    v-if="participant.is_controller" 
                    size="x-small" 
                    color="primary" 
                    class="ml-2"
                  >
                    Host
                  </v-chip>
                </v-list-item-title>
                
                <v-list-item-subtitle>
                  ID: {{ participant.participant_id.slice(0, 8) }}...
                </v-list-item-subtitle>
                
                <template v-slot:append v-if="!participant.is_controller && isController">
                  <v-tooltip text="Remove participant from room">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        v-bind="props"
                        icon="mdi-account-remove"
                        size="small"
                        color="error"
                        variant="text"
                        @click="kickParticipant(participant.participant_id)"
                      />
                    </template>
                  </v-tooltip>
                </template>
              </v-list-item>
            </v-list>
            
            <v-divider class="my-3" />
            
            <v-btn
              block
              color="primary"
              variant="outlined"
              @click="showRoomInfo = true"
            >
              <v-icon class="mr-2">mdi-information</v-icon>
              Room Information
            </v-btn>
          </v-card-text>
        </v-card>
      </v-menu>
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
                    <div class="text-center text-caption mt-1">Scroll Forward</div>
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
                      <div class="text-center text-caption mt-1">Previous Section</div>
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
                      <div class="text-center text-caption mt-1">Next Section</div>
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
                    <v-btn 
                      color="primary" 
                      @click="goToEnd"
                      block
                      size="large"
                    >
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
                    No sections could be parsed from the script.<br>
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
                      <v-icon>{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
                      <span class="ml-2">{{ isPlaying ? 'Pause' : 'Start' }}</span>
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
                      @click="scrollSpeed = Math.max(0.1, Math.round((scrollSpeed - 0.1) * 10) / 10); updateSpeed()"
                    />
                  </template>
                  <template v-slot:append-inner>
                    <v-btn 
                      icon="mdi-plus" 
                      size="x-small" 
                      variant="text"
                      @click="scrollSpeed = Math.min(10, Math.round((scrollSpeed + 0.1) * 10) / 10); updateSpeed()"
                    />
                  </template>
                </v-text-field>

                <!-- Sync Text Button -->
                <v-btn 
                  color="primary" 
                  @click="syncText"
                  class="mt-3"
                  block
                >
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
                            @click="aiScrolling.config.look_ahead_chars = Math.max(50, aiScrolling.config.look_ahead_chars - 10); updateAIScrollingConfig()"
                          />
                        </template>
                        <template v-slot:append-inner>
                          <v-btn 
                            icon="mdi-plus" 
                            size="x-small" 
                            variant="text"
                            @click="aiScrolling.config.look_ahead_chars = Math.min(500, aiScrolling.config.look_ahead_chars + 10); updateAIScrollingConfig()"
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
                            @click="aiScrolling.config.look_behind_chars = Math.max(25, aiScrolling.config.look_behind_chars - 5); updateAIScrollingConfig()"
                          />
                        </template>
                        <template v-slot:append-inner>
                          <v-btn 
                            icon="mdi-plus" 
                            size="x-small" 
                            variant="text"
                            @click="aiScrolling.config.look_behind_chars = Math.min(200, aiScrolling.config.look_behind_chars + 5); updateAIScrollingConfig()"
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
                        v-model.number="aiScrolling.config.pause_threshold_seconds"
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
                            @click="aiScrolling.config.pause_threshold_seconds = Math.max(1.0, Math.round((aiScrolling.config.pause_threshold_seconds - 0.5) * 10) / 10); updateAIScrollingConfig()"
                          />
                        </template>
                        <template v-slot:append-inner>
                          <v-btn 
                            icon="mdi-plus" 
                            size="x-small" 
                            variant="text"
                            @click="aiScrolling.config.pause_threshold_seconds = Math.min(10.0, Math.round((aiScrolling.config.pause_threshold_seconds + 0.5) * 10) / 10); updateAIScrollingConfig()"
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
                    <v-icon start size="small">{{ aiScrolling.status.icon }}</v-icon>
                    {{ aiScrolling.status.text }}
                  </v-chip>
                </div>
              </v-card-text>
              
              <v-card-text v-else>
                <div v-if="!aiScrolling.available" class="text-caption text-error text-center">
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
                      @click="textWidth = Math.max(20, textWidth - 5); updateWidth()"
                    />
                  </template>
                  <template v-slot:append-inner>
                    <v-btn 
                      icon="mdi-plus" 
                      size="x-small" 
                      variant="text"
                      @click="textWidth = Math.min(100, textWidth + 5); updateWidth()"
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
                      @click="fontSize = Math.max(0.5, Math.round((fontSize - 0.1) * 10) / 10); updateFontSize()"
                    />
                  </template>
                  <template v-slot:append-inner>
                    <v-btn 
                      icon="mdi-plus" 
                      size="x-small" 
                      variant="text"
                      @click="fontSize = Math.min(5, Math.round((fontSize + 0.1) * 10) / 10); updateFontSize()"
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

    <v-snackbar 
      v-model="snackbar.show" 
      :color="snackbar.color"
      location="top center"
      :timeout="4000"
    >
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">
          Close
        </v-btn>
      </template>
    </v-snackbar>

    <!-- Room Info Dialog -->
    <v-dialog v-model="showRoomInfo" max-width="600px">
      <v-card>
        <v-card-title class="pa-6">
          <v-icon class="mr-2">mdi-information</v-icon>
          Room Information
        </v-card-title>
        
        <v-card-text class="pa-6 pt-0">
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                label="Room ID"
                :model-value="channelName"
                readonly
                variant="outlined"
                density="compact"
              >
                <template v-slot:append-inner>
                  <v-btn
                    icon="mdi-content-copy"
                    size="small"
                    variant="text"
                    @click="copyToClipboard(channelName, 'Room ID copied!')"
                  />
                </template>
              </v-text-field>
            </v-col>
            
            <v-col cols="12" sm="6">
              <v-text-field
                label="Room Secret"
                :model-value="roomSecret"
                readonly
                variant="outlined"
                density="compact"
              >
                <template v-slot:append-inner>
                  <v-btn
                    icon="mdi-content-copy"
                    size="small"
                    variant="text"
                    @click="copyToClipboard(roomSecret, 'Room Secret copied!')"
                  />
                </template>
              </v-text-field>
            </v-col>
          </v-row>
          
          <v-divider class="my-4" />
          
          <h4 class="text-h6 mb-3">Quick Join Options</h4>
          
          <v-alert type="info" variant="tonal" class="mb-4">
            <strong>Share this URL:</strong> Anyone can use this link to join directly as a teleprompter.
          </v-alert>
          
          <v-text-field
            label="Direct Join URL"
            :model-value="joinUrl"
            readonly
            variant="outlined"
            density="compact"
            class="mb-4"
          >
            <template v-slot:append-inner>
              <v-btn
                icon="mdi-content-copy"
                size="small"
                variant="text"
                @click="copyToClipboard(joinUrl, 'Join URL copied!')"
              />
            </template>
          </v-text-field>
          
          <div class="text-center">
            <div class="qr-code-container">
              <img :src="qrCodeUrl" alt="QR Code for room joining" class="qr-code-image-large" />
              <p class="text-caption mt-2">Scan to join as teleprompter</p>
            </div>
          </div>
        </v-card-text>
        
        <v-card-actions class="pa-6 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="showRoomInfo = false">
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script>
import { config } from '@/utils/config.js'
import { 
  parseMarkdownSections, 
  getCurrentSection, 
  getNextSection, 
  getPreviousSection,
  generateTableOfContents 
} from '@/utils/markdown.js'

export default {
  name: 'Controller',
  
  data() {
    return {
      // Connection state
      ws: null,
      channelName: '',
      roomName: '',
      roomSecret: '',
      connectionInfo: {
        show: false,
        count: 0
      },
      
      // Room info
      roomInfo: {
        participants: []
      },
      showRoomInfo: false,
      
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
        text: '',
        color: 'success'
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
          audio_source: 'controller'
        },
        status: {
          color: 'default',
          icon: 'mdi-microphone-off',
          text: 'AI Scrolling Disabled'
        }
      },
      
      // Audio recording state
      audioRecording: {
        active: false,
        mediaRecorder: null,
        stream: null
      }
    }
  },
  
  computed: {
    // Check if current user is the controller
    isController() {
      const currentParticipant = this.roomInfo.participants.find(p => p.is_controller)
      return currentParticipant && currentParticipant.mode === 'controller'
    },
    
    // Generate join URL for sharing
    joinUrl() {
      const baseUrl = window.location.origin
      return `${baseUrl}/teleprompter?room=${this.channelName}&secret=${this.roomSecret}`
    },
    
    // Auto-generate QR code URL
    qrCodeUrl() {
      if (!this.joinUrl) return ''
      const qrText = encodeURIComponent(this.joinUrl)
      return `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${qrText}`
    },
    
    // Audio source options for AI scrolling
    audioSourceOptions() {
      return [
        { title: 'Controller (This Device)', value: 'controller' },
        { title: 'Teleprompter Device', value: 'teleprompter' }
      ]
    },
    
    // Parse markdown sections from script text
    sections() {
      return parseMarkdownSections(this.scriptText)
    },
    
    // Current section based on scroll position
    currentSection() {
      return getCurrentSection(this.sections, this.currentScrollPosition)
    },
    
    // Check if can navigate to previous section
    canGoToPreviousSection() {
      return getPreviousSection(this.sections, this.currentScrollPosition) !== null
    },
    
    // Check if can navigate to next section
    canGoToNextSection() {
      return getNextSection(this.sections, this.currentScrollPosition) !== null
    }
  },
  
  mounted() {
    // Get channel name and secret from URL params
    this.channelName = this.$route.query.room || 'default'
    this.roomSecret = this.$route.query.secret || ''
    
    // Fetch room information to get room name
    this.fetchRoomInfo()
    
    // Check AI scrolling availability
    this.checkAIScrollingAvailability()
    
    // Connect to WebSocket
    this.connect()
  },
  
  beforeUnmount() {
    // Clean up audio recording
    if (this.audioRecording.active) {
      this.stopAudioRecording()
    }
    
    if (this.ws) {
      this.ws.close()
    }
  },
  
  methods: {
    async fetchRoomInfo() {
      try {
        const response = await fetch(`${config.getApiUrl()}/api/rooms/${this.channelName}`)
        if (response.ok) {
          const roomData = await response.json()
          this.roomName = roomData.room_name || this.channelName
        }
      } catch (error) {
        console.warn('Could not fetch room info:', error)
        // Fallback to using channelName
      }
    },
    
    async checkAIScrollingAvailability() {
      try {
        // Check if microphone access is available
        const hasMediaDevices = navigator.mediaDevices && navigator.mediaDevices.getUserMedia
        
        if (hasMediaDevices) {
          // Check with backend if AI scrolling is available
          const response = await fetch(`${config.getApiUrl()}/api/channel/${this.channelName}/ai-scrolling`)
          const data = await response.json()
          this.aiScrolling.available = data.available || false
        } else {
          this.aiScrolling.available = false
        }
        
      } catch (error) {
        console.warn('Could not check AI scrolling availability:', error)
        this.aiScrolling.available = false
      }
    },
    
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
        
        // Send authentication first
        this.sendMessage({
          type: 'authenticate',
          room_id: this.channelName,
          secret: this.roomSecret,
          mode: 'controller'
        })
      }
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('Received message:', message)
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
        case 'auth_success':
          console.log('Authentication successful')
          this.showSnackbar('Connected to teleprompter channel', 'success')
          
          // Sync initial settings after successful authentication
          setTimeout(() => {
            this.syncText()
            this.updateSpeed()
            this.updateHorizontalMirror()
            this.updateVerticalMirror()
            this.updateFontSize()
            this.updateWidth()
          }, 500)
          
          // Request room info
          setTimeout(() => {
            this.sendMessage({ type: 'request_connection_info' })
          }, 1000)
          break
          
        case 'auth_error':
          console.error('Authentication failed:', message.message)
          this.showSnackbar(`Authentication failed: ${message.message}`, 'error')
          // Redirect back to landing page
          this.$router.push('/')
          break
          
        case 'room_update':
          // Check for new participants joining
          const currentParticipantIds = new Set(this.roomInfo.participants.map(p => p.participant_id))
          const newParticipantIds = new Set((message.participants || []).map(p => p.participant_id))
          
          // Find newly joined participants
          const joinedParticipants = (message.participants || []).filter(p => 
            !currentParticipantIds.has(p.participant_id) && p.mode === 'teleprompter'
          )
          
          // Show notification for new teleprompter joins
          if (joinedParticipants.length > 0) {
            const newCount = joinedParticipants.length
            this.showSnackbar(
              newCount === 1 
                ? 'New teleprompter joined the room' 
                : `${newCount} new teleprompters joined the room`, 
              'info'
            )
          }
          
          this.connectionInfo.count = message.participant_count
          this.connectionInfo.show = true
          this.roomInfo.participants = message.participants || []
          break
          
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
          // Update width when teleprompter changes width setting
          this.textWidth = message.value
          break
          
        case 'font_size':
          // Update font size when teleprompter changes font size
          this.fontSize = message.value
          break
          
        case 'ai_scrolling_started':
          this.aiScrolling.status = {
            color: 'success',
            icon: 'mdi-microphone',
            text: 'AI Scrolling Active'
          }
          this.showSnackbar('AI Scrolling started', 'success')
          break
          
        case 'ai_scrolling_stopped':
          this.aiScrolling.status = {
            color: 'default',
            icon: 'mdi-microphone-off',
            text: 'AI Scrolling Disabled'
          }
          this.showSnackbar('AI Scrolling stopped', 'info')
          break
          
        case 'ai_scrolling_config_updated':
          this.aiScrolling.config = { ...message.config }
          break
          
        case 'ai_scrolling_error':
          this.aiScrolling.status = {
            color: 'error',
            icon: 'mdi-alert',
            text: `AI Error: ${message.error}`
          }
          this.showSnackbar(`AI Scrolling Error: ${message.error}`, 'error')
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
    
    // Playback controls
    togglePlayback() {
      if (this.isPlaying) {
        this.pauseScrolling()
      } else {
        this.startScrolling()
      }
    },
    
    startScrolling() {
      this.isPlaying = true
      this.sendMessage({ type: 'start' })
      this.showSnackbar('Teleprompter started', 'success')
    },
    
    pauseScrolling() {
      this.isPlaying = false
      this.sendMessage({ type: 'pause' })
      this.showSnackbar('Teleprompter paused', 'warning')
    },

    // Navigation controls
    goToBeginning() {
      this.sendMessage({ type: 'go_to_beginning' })
    },

    goToEnd() {
      this.sendMessage({ type: 'go_to_end' })
    },

    scrollBackLines() {
      this.sendMessage({ 
        type: 'scroll_lines', 
        direction: 'back',
        lines: this.scrollLines 
      })
    },

    scrollForwardLines() {
      this.sendMessage({ 
        type: 'scroll_lines', 
        direction: 'forward',
        lines: this.scrollLines 
      })
    },

    // Section navigation controls
    goToPreviousSection() {
      const prevSection = getPreviousSection(this.sections, this.currentScrollPosition)
      if (prevSection) {
        this.goToSection(prevSection)
      }
    },

    goToNextSection() {
      const nextSection = getNextSection(this.sections, this.currentScrollPosition)
      if (nextSection) {
        this.goToSection(nextSection)
      }
    },

    goToSection(section) {
      this.currentScrollPosition = section.start
      this.sendMessage({ 
        type: 'go_to_section', 
        sectionLine: section.start,
        sectionTitle: section.title 
      })
    },
    
    // Text sync
    syncText() {
      this.sendMessage({ 
        type: 'text', 
        content: this.scriptText 
      })
      this.showSnackbar('Text synced to teleprompters', 'success')
    },
    
    debouncedSyncText() {
      clearTimeout(this.syncTimeout)
      this.syncTimeout = setTimeout(() => {
        this.syncText()
      }, 1000)
    },
    
    // Speed controls
    updateSpeed() {
      this.sendMessage({ 
        type: 'speed', 
        value: this.scrollSpeed 
      })
    },
    
    // Font size controls
    updateFontSize() {
      this.sendMessage({ 
        type: 'font_size', 
        value: this.fontSize 
      })
    },
    
    // Width controls
    updateWidth() {
      this.sendMessage({ 
        type: 'width', 
        value: this.textWidth 
      })
    },
    
    // Mirror controls
    toggleHorizontalMirror() {
      this.horizontalMirror = !this.horizontalMirror
      this.updateHorizontalMirror()
    },

    toggleVerticalMirror() {
      this.verticalMirror = !this.verticalMirror
      this.updateVerticalMirror()
    },

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
    
    // AI Scrolling methods
    async toggleAIScrolling() {
      if (this.aiScrolling.enabled) {
        await this.startAIScrolling()
      } else {
        await this.stopAIScrolling()
      }
    },
    
    async startAIScrolling() {
      try {
        // Check if we need to start audio recording
        if (this.aiScrolling.config.audio_source === 'controller') {
          await this.startAudioRecording()
        }
        
        // Start AI scrolling session
        this.sendMessage({
          type: 'ai_scrolling_start',
          script_content: this.scriptText,
          config: this.aiScrolling.config
        })
        
        this.aiScrolling.status = {
          color: 'info',
          icon: 'mdi-loading',
          text: 'Starting AI Scrolling...'
        }
        
      } catch (error) {
        console.error('Error starting AI scrolling:', error)
        // Don't disable the UI checkbox, just show error status
        this.aiScrolling.status = {
          color: 'error',
          icon: 'mdi-alert',
          text: `Error: ${error.message}`
        }
        this.showSnackbar(`Failed to start AI scrolling: ${error.message}`, 'error')
      }
    },
    
    async stopAIScrolling() {
      try {
        // Stop audio recording if active
        if (this.audioRecording.active) {
          this.stopAudioRecording()
        }
        
        // Stop AI scrolling session
        this.sendMessage({
          type: 'ai_scrolling_stop'
        })
        
        this.aiScrolling.status = {
          color: 'default',
          icon: 'mdi-microphone-off',
          text: 'AI Scrolling Disabled'
        }
        
      } catch (error) {
        console.error('Error stopping AI scrolling:', error)
        this.showSnackbar(`Error stopping AI scrolling: ${error.message}`, 'error')
      }
    },
    
    updateAIScrollingConfig() {
      if (this.aiScrolling.enabled) {
        this.sendMessage({
          type: 'ai_scrolling_config',
          ...this.aiScrolling.config
        })
      }
    },
    
    async startAudioRecording() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true
          } 
        })
        
        this.audioRecording.stream = stream
        this.audioRecording.mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus'
        })
        
        this.audioRecording.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && this.aiScrolling.enabled) {
            this.sendAudioChunk(event.data)
          }
        }
        
        // Record in small chunks for real-time processing
        this.audioRecording.mediaRecorder.start(1000) // 1 second chunks
        this.audioRecording.active = true
        
      } catch (error) {
        throw new Error(`Microphone access denied: ${error.message}`)
      }
    },
    
    stopAudioRecording() {
      if (this.audioRecording.mediaRecorder) {
        this.audioRecording.mediaRecorder.stop()
        this.audioRecording.mediaRecorder = null
      }
      
      if (this.audioRecording.stream) {
        this.audioRecording.stream.getTracks().forEach(track => track.stop())
        this.audioRecording.stream = null
      }
      
      this.audioRecording.active = false
    },
    
    async sendAudioChunk(audioBlob) {
      try {
        const arrayBuffer = await audioBlob.arrayBuffer()
        const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))
        
        this.sendMessage({
          type: 'audio_chunk',
          audio_data: base64Audio
        })
        
      } catch (error) {
        console.error('Error sending audio chunk:', error)
      }
    },
    
    // Utility methods
    disconnect() {
      if (this.ws) {
        this.ws.close()
      }
      // Navigate back to landing page using Vue Router
      this.$router.push('/')
    },
    
    // Room management methods
    kickParticipant(participantId) {
      this.sendMessage({
        type: 'kick_participant',
        target_participant_id: participantId
      })
      this.showSnackbar('Participant removed from room', 'warning')
    },
    
    async copyToClipboard(text, message) {
      try {
        await navigator.clipboard.writeText(text)
        this.showSnackbar(message, 'success')
      } catch (err) {
        this.showSnackbar('Failed to copy to clipboard', 'error')
      }
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

.qr-code-container {
  display: inline-block;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.qr-code-image {
  max-width: 200px;
  height: auto;
  display: block;
}

.qr-code-image-large {
  max-width: 300px;
  height: auto;
  display: block;
}
</style>