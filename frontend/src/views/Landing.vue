<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>Remote Teleprompter</v-toolbar-title>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height">
        <v-row justify="center" align="center" class="fill-height">
          <v-col cols="12" md="8" lg="6">
            
            <!-- Main Action Card -->
            <v-card elevation="8">
              <v-card-title class="text-h5 pa-6">
                <v-icon class="mr-2">mdi-account-group</v-icon>
                Welcome to Remote Teleprompter
              </v-card-title>

              <v-card-text class="pa-6">
                <p class="text-body-1 mb-6">
                  Choose your action to get started with remote teleprompter control.
                </p>
                
                <v-row class="mb-4">
                  <!-- Create Room (Controller) -->
                  <v-col cols="12" md="6">
                    <v-card
                      class="action-card"
                      :class="{ selected: selectedAction === 'create' }"
                      @click="selectedAction = 'create'"
                      elevation="2"
                      hover
                    >
                      <v-card-text class="text-center pa-6">
                        <v-icon size="48" color="primary" class="mb-2">mdi-plus-circle</v-icon>
                        <h4 class="text-h6 mb-2">💻 Create Room</h4>
                        <p class="text-body-2">
                          Create a new room and control teleprompter playback
                        </p>
                      </v-card-text>
                    </v-card>
                  </v-col>

                  <!-- Join Room (Teleprompter) -->
                  <v-col cols="12" md="6">
                    <v-card
                      class="action-card"
                      :class="{ selected: selectedAction === 'join' }"
                      @click="selectedAction = 'join'"
                      elevation="2"
                      hover
                    >
                      <v-card-text class="text-center pa-6">
                        <v-icon size="48" color="primary" class="mb-2">mdi-login</v-icon>
                        <h4 class="text-h6 mb-2">📱 Join Room</h4>
                        <p class="text-body-2">
                          Join an existing room to display teleprompter text
                        </p>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- Create Room Form -->
                <v-expand-transition>
                  <div v-if="selectedAction === 'create'">
                    <v-divider class="my-4" />
                    <h3 class="text-h6 mb-4">Create New Room</h3>
                    
                    <v-text-field
                      v-model="roomName"
                      label="Room Name (Optional)"
                      placeholder="Leave blank for auto-generated name"
                      prepend-icon="mdi-tag"
                      variant="outlined"
                      class="mb-4"
                      @keypress.enter="createRoom"
                    />

                    <v-btn
                      block
                      color="primary"
                      size="large"
                      @click="createRoom"
                      :loading="loading"
                      :disabled="loading"
                    >
                      <v-icon class="mr-2">mdi-plus</v-icon>
                      Create Room & Start Controlling
                    </v-btn>
                  </div>
                </v-expand-transition>

                <!-- Join Room Form -->
                <v-expand-transition>
                  <div v-if="selectedAction === 'join'">
                    <v-divider class="my-4" />
                    <h3 class="text-h6 mb-4">Join Existing Room</h3>
                    
                    <v-text-field
                      v-model="joinRoomId"
                      label="Room ID"
                      placeholder="Enter room ID (e.g., roomabc12345)"
                      prepend-icon="mdi-key"
                      variant="outlined"
                      class="mb-4"
                      @keypress.enter="joinRoom"
                    />

                    <v-text-field
                      v-model="joinRoomSecret"
                      label="Room Secret"
                      placeholder="Enter room secret"
                      prepend-icon="mdi-lock"
                      variant="outlined"
                      class="mb-4"
                      type="password"
                      @keypress.enter="joinRoom"
                    />

                    <v-row class="mb-4">
                      <v-col cols="6">
                        <v-btn
                          block
                          color="secondary"
                          variant="outlined"
                          size="large"
                          @click="pasteCredentials"
                        >
                          <v-icon class="mr-2">mdi-content-paste</v-icon>
                          Paste from Clipboard
                        </v-btn>
                      </v-col>
                      <v-col cols="6">
                        <v-btn
                          block
                          color="primary"
                          size="large"
                          @click="joinRoom"
                          :loading="loading"
                          :disabled="!joinRoomId || !joinRoomSecret || loading"
                        >
                          <v-icon class="mr-2">mdi-login</v-icon>
                          Join as Teleprompter
                        </v-btn>
                      </v-col>
                    </v-row>
                  </div>
                </v-expand-transition>

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

export default {
  name: "Landing",
  data() {
    return {
      selectedAction: "",
      
      // Create room data
      roomName: "",
      loading: false,
      
      // Join room data
      joinRoomId: "",
      joinRoomSecret: "",
      
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },
      
      // Room name generation
      adjectives: [
        "Bright", "Swift", "Calm", "Brave", "Quick", "Gentle", "Sharp", "Bold", 
        "Clever", "Strong", "Wise", "Kind", "Happy", "Peaceful", "Dynamic", "Elegant",
        "Graceful", "Lively", "Vibrant", "Steady", "Creative", "Focused", "Reliable"
      ],
      animals: [
        "Wolf", "Eagle", "Lion", "Bear", "Fox", "Hawk", "Tiger", "Dolphin",
        "Owl", "Falcon", "Panther", "Shark", "Horse", "Dragon", "Phoenix", "Whale",
        "Rabbit", "Deer", "Elephant", "Giraffe", "Penguin", "Turtle", "Butterfly"
      ]
    };
  },

  methods: {
    generateRoomName() {
      const adjective = this.adjectives[Math.floor(Math.random() * this.adjectives.length)];
      const animal = this.animals[Math.floor(Math.random() * this.animals.length)];
      return `${adjective} ${animal} Room`;
    },

    async createRoom() {
      // Generate room name if not provided
      if (!this.roomName) {
        this.roomName = this.generateRoomName();
      }
      
      this.loading = true;
      try {
        const apiUrl = config.getApiUrl();
        const response = await fetch(`${apiUrl}/api/rooms`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            room_name: this.roomName
          })
        });

        if (!response.ok) {
          throw new Error('Failed to create room');
        }

        const roomData = await response.json();
        
        // Store room credentials in session storage for the controller
        sessionStorage.setItem('room_credentials', JSON.stringify({
          room_id: roomData.room_id,
          room_secret: roomData.room_secret,
          room_name: roomData.room_name,
          role: 'controller'
        }));

        // Navigate to controller with room info
        this.$router.push({
          path: "/controller",
          query: { 
            room: roomData.room_id,
            role: 'controller'
          },
        });

      } catch (error) {
        console.error('Error creating room:', error);
        this.showSnackbar('Failed to create room. Please try again.', 'error');
      } finally {
        this.loading = false;
      }
    },

    async joinRoom() {
      this.loading = true;
      try {
        const apiUrl = config.getApiUrl();
        const response = await fetch(`${apiUrl}/api/rooms/join`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            room_id: this.joinRoomId,
            room_secret: this.joinRoomSecret,
            role: 'teleprompter'
          })
        });

        if (!response.ok) {
          throw new Error('Failed to join room');
        }

        const joinData = await response.json();
        
        if (!joinData.success) {
          this.showSnackbar(joinData.message, 'error');
          return;
        }

        // Store room credentials in session storage for the teleprompter
        sessionStorage.setItem('room_credentials', JSON.stringify({
          room_id: this.joinRoomId,
          room_secret: this.joinRoomSecret,
          room_name: joinData.room_name,
          participant_id: joinData.participant_id,
          role: 'teleprompter'
        }));

        // Navigate to teleprompter with room info
        this.$router.push({
          path: "/teleprompter",
          query: { 
            room: this.joinRoomId,
            role: 'teleprompter'
          },
        });

      } catch (error) {
        console.error('Error joining room:', error);
        this.showSnackbar('Failed to join room. Please check your credentials.', 'error');
      } finally {
        this.loading = false;
      }
    },

    async pasteCredentials() {
      try {
        const text = await navigator.clipboard.readText();
        if (text.trim()) {
          // Try to parse as JSON for full credentials
          try {
            const credentials = JSON.parse(text);
            if (credentials.room_id && credentials.room_secret) {
              this.joinRoomId = credentials.room_id;
              this.joinRoomSecret = credentials.room_secret;
              this.showSnackbar("Room credentials pasted!", "success");
              return;
            }
          } catch (e) {
            // Not JSON, try to parse as simple room ID
          }

          // If it looks like a room ID, just paste that
          if (text.includes('room')) {
            this.joinRoomId = text.trim();
            this.showSnackbar("Room ID pasted! Please enter the room secret.", "info");
          } else {
            this.showSnackbar("Pasted text doesn't look like room credentials.", "warning");
          }
        }
      } catch (err) {
        this.showSnackbar(
          "Could not access clipboard. Please paste manually.",
          "warning"
        );
      }
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
.action-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.action-card:hover {
  transform: translateY(-2px);
}

.action-card.selected {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
