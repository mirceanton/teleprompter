<template>
  <v-app>
    <v-main>
      <div class="landing-container">
        <!-- Background with gradient -->
        <div class="background-gradient"></div>
        
        <v-container fluid class="fill-height">
          <v-row justify="center" align="center" class="fill-height">
            <v-col cols="12" md="8" lg="6" xl="5">
              
              <!-- Hero Section -->
              <div class="hero-section text-center mb-8">
                <div class="hero-icon-container mb-4">
                  <v-avatar size="120" class="hero-avatar">
                    <v-icon size="64" color="white">mdi-message-text-outline</v-icon>
                  </v-avatar>
                </div>
                <h1 class="hero-title mb-3">Remote Teleprompter</h1>
                <p class="hero-subtitle">
                  Professional teleprompter control between your devices
                </p>
              </div>

              <!-- Main Card -->
              <v-card class="main-card" elevation="16">
                
                <!-- Room Setup Section -->
                <v-card-title class="section-title">
                  <div class="section-header">
                    <v-icon class="section-icon">mdi-account-group-outline</v-icon>
                    <span>Join or Create Room</span>
                  </div>
                </v-card-title>
                
                <v-card-text class="card-content">
                  <!-- Room ID Input -->
                  <div class="input-section mb-6">
                    <v-text-field
                      v-model="channelName"
                      label="Room ID"
                      placeholder="Enter room ID or generate a new one"
                      prepend-inner-icon="mdi-key-variant"
                      variant="outlined"
                      color="primary"
                      class="room-input"
                      @keypress.enter="handleJoin"
                      hide-details
                    />

                    <div class="action-buttons mt-3">
                      <v-btn
                        color="secondary"
                        variant="outlined"
                        size="small"
                        @click="generateRoomId"
                        class="action-btn"
                      >
                        <v-icon start size="small">mdi-refresh</v-icon>
                        Generate
                      </v-btn>
                      <v-btn
                        color="info"
                        variant="outlined"
                        size="small"
                        @click="pasteRoomId"
                        class="action-btn"
                      >
                        <v-icon start size="small">mdi-content-paste</v-icon>
                        Paste
                      </v-btn>
                    </div>
                  </div>

                  <!-- Role Selection -->
                  <div class="role-selection">
                    <h3 class="role-title mb-4">Choose Your Device Role</h3>

                    <v-row class="role-cards">
                      <v-col cols="6">
                        <div
                          class="role-card"
                          :class="{ 'selected': selectedRole === 'controller' }"
                          @click="selectedRole = 'controller'"
                        >
                          <div class="role-icon-container">
                            <v-icon class="role-icon">mdi-laptop</v-icon>
                          </div>
                          <h4 class="role-name">Controller</h4>
                          <p class="role-description">
                            Edit scripts & control playback
                          </p>
                        </div>
                      </v-col>
                      
                      <v-col cols="6">
                        <div
                          class="role-card"
                          :class="{ 'selected': selectedRole === 'teleprompter' }"
                          @click="selectedRole = 'teleprompter'"
                        >
                          <div class="role-icon-container">
                            <v-icon class="role-icon">mdi-tablet</v-icon>
                          </div>
                          <h4 class="role-name">Display</h4>
                          <p class="role-description">
                            Show scrolling text
                          </p>
                        </div>
                      </v-col>
                    </v-row>
                  </div>

                  <!-- Join Button -->
                  <v-btn
                    block
                    color="primary"
                    size="x-large"
                    class="join-button"
                    @click="handleJoin"
                    :disabled="!channelName || !selectedRole"
                    elevation="4"
                  >
                    <v-icon start size="large">mdi-rocket-launch</v-icon>
                    Launch Session
                  </v-btn>
                </v-card-text>
              </v-card>

            </v-col>
          </v-row>
        </v-container>
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
  name: 'Landing',
  data() {
    return {
      channelName: '',
      selectedRole: '',
      snackbar: {
        show: false,
        text: '',
        color: 'success'
      }
    }
  },
  
  mounted() {
    // Generate initial room ID
    this.generateRoomId()
  },
  
  methods: {
    generateRoomId() {
      this.channelName = 'room-' + Math.random().toString(36).substring(2, 8)
      this.showSnackbar('New room ID generated!', 'success')
    },
    
    async pasteRoomId() {
      try {
        const text = await navigator.clipboard.readText()
        if (text.trim()) {
          this.channelName = text.trim()
          this.showSnackbar('Room ID pasted!', 'success')
        }
      } catch (err) {
        this.showSnackbar('Could not access clipboard. Please paste manually.', 'warning')
      }
    },
    
    handleJoin() {
      if (!this.channelName || !this.selectedRole) {
        this.showSnackbar('Please enter a room ID and select a role.', 'error')
        return
      }
      
      // Navigate using Vue Router instead of window.location.href
      if (this.selectedRole === 'controller') {
        this.$router.push({ path: '/controller', query: { room: this.channelName } })
      } else {
        this.$router.push({ path: '/teleprompter', query: { room: this.channelName } })
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
.landing-container {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.background-gradient {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: -1;
}

.fill-height {
  min-height: 100vh;
}

/* Hero Section */
.hero-section {
  margin-bottom: 2rem;
}

.hero-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  border: 3px solid rgba(255, 255, 255, 0.2);
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
  margin-bottom: 1rem;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 300;
  text-shadow: 0 1px 10px rgba(0, 0, 0, 0.2);
}

/* Main Card */
.main-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 24px !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.section-title {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 1.5rem 2rem !important;
  margin: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.section-icon {
  font-size: 1.5rem;
}

.card-content {
  padding: 2rem !important;
}

/* Input Section */
.input-section {
  background: rgba(102, 126, 234, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.room-input :deep(.v-field) {
  border-radius: 12px;
  background: white;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.action-btn {
  border-radius: 8px !important;
  text-transform: none;
  font-weight: 500;
}

/* Role Selection */
.role-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #2d3748;
  text-align: center;
}

.role-cards {
  gap: 1rem;
}

.role-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.5rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.role-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 0;
}

.role-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
  border-color: #667eea;
}

.role-card.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
}

.role-card.selected::before {
  opacity: 1;
}

.role-card > * {
  position: relative;
  z-index: 1;
}

.role-icon-container {
  margin-bottom: 0.75rem;
}

.role-icon {
  font-size: 2.5rem;
  color: #667eea;
  transition: color 0.3s ease;
}

.role-card.selected .role-icon {
  color: white;
}

.role-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #2d3748;
  transition: color 0.3s ease;
}

.role-card.selected .role-name {
  color: white;
}

.role-description {
  font-size: 0.875rem;
  color: #718096;
  margin: 0;
  line-height: 1.4;
  transition: color 0.3s ease;
}

.role-card.selected .role-description {
  color: rgba(255, 255, 255, 0.9);
}

/* Join Button */
.join-button {
  margin-top: 2rem !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 12px !important;
  font-weight: 600;
  font-size: 1.1rem;
  text-transform: none;
  height: 56px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.join-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
}

.join-button:disabled {
  opacity: 0.6;
  transform: none !important;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2) !important;
}

/* Responsive adjustments */
@media (max-width: 960px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.125rem;
  }
  
  .card-content {
    padding: 1.5rem !important;
  }
  
  .input-section {
    padding: 1rem;
  }
  
  .role-card {
    padding: 1rem 0.75rem;
  }
}

@media (max-width: 600px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .role-cards .v-col {
    padding: 0.5rem;
  }
}
</style>