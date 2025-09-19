<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>Remote Teleprompter </v-toolbar-title>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height">
        <v-row justify="center" align="center" class="fill-height">
          <v-col cols="12" md="8" lg="6">
            <!-- Main Options Card -->
            <v-card elevation="8">
              <v-card-title class="text-h5 pa-6">
                <v-icon class="mr-2">mdi-account-group</v-icon>
                Remote Teleprompter
              </v-card-title>

              <v-card-text class="pa-6">
                <p class="text-body-1 mb-6">
                  Create a new teleprompter room or join an existing one.
                </p>

                <v-row>
                  <v-col cols="12" md="6">
                    <v-card
                      class="action-card"
                      elevation="2"
                      hover
                      @click="showCreateRoom = true"
                    >
                      <v-card-text class="text-center pa-6">
                        <v-icon size="48" color="primary" class="mb-2"
                          >mdi-plus-circle</v-icon
                        >
                        <h4 class="text-h6 mb-2">Create New Room</h4>
                        <p class="text-body-2">
                          Start a new teleprompter session as the controller.
                        </p>
                      </v-card-text>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-card
                      class="action-card"
                      elevation="2"
                      hover
                      @click="showJoinRoom = true"
                    >
                      <v-card-text class="text-center pa-6">
                        <v-icon size="48" color="secondary" class="mb-2"
                          >mdi-login</v-icon
                        >
                        <h4 class="text-h6 mb-2">Join Existing Room</h4>
                        <p class="text-body-2">
                          Join an existing teleprompter session as a prompter
                          display.
                        </p>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Create Room Dialog -->
    <v-dialog v-model="showCreateRoom" max-width="600px" persistent>
      <v-card>
        <v-card-title class="pa-6">Create New Room</v-card-title>

        <v-card-text class="pa-6 pt-0">
          <v-text-field
            v-model="createForm.roomName"
            label="Room Name"
            prepend-inner-icon="mdi-rename-box"
            variant="outlined"
            class="mb-4"
          />
          <hr />
          <br />
          <v-text-field
            label="Room ID"
            :model-value="roomPreview.roomId"
            readonly
            disabled
            variant="solo"
            density="compact"
            class="greyed-out"
            prepend-inner-icon="mdi-identifier"
          />
          <v-text-field
            label="Room Password"
            :model-value="roomPreview.secret"
            readonly
            disabled
            variant="solo"
            density="compact"
            class="greyed-out"
            prepend-inner-icon="mdi-lock"
          />
        </v-card-text>

        <v-card-actions class="pa-6 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="cancelCreateRoom"> Cancel </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="createRoom"
            :loading="creating"
          >
            Create Room
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Join Room Dialog -->
    <v-dialog v-model="showJoinRoom" max-width="600px">
      <v-card>
        <v-card-title class="pa-6">
          <v-icon class="mr-2">mdi-login</v-icon>
          Join Existing Room
        </v-card-title>

        <v-card-text class="pa-6 pt-0">
          <v-text-field
            v-model="joinForm.roomId"
            label="Room ID"
            placeholder="e.g., room-abc123"
            prepend-icon="mdi-key"
            variant="outlined"
            class="mb-4"
            :error-messages="joinErrors.roomId"
          />

          <v-text-field
            v-model="joinForm.secret"
            label="Room Secret"
            placeholder="e.g., ABC12345"
            prepend-icon="mdi-lock"
            variant="outlined"
            class="mb-4"
            :error-messages="joinErrors.secret"
          />

          <v-row class="mb-4">
            <v-col cols="6">
              <v-btn
                block
                color="secondary"
                variant="outlined"
                @click="pasteCredentials"
              >
                <v-icon class="mr-2">mdi-content-paste</v-icon>
                Paste Credentials
              </v-btn>
            </v-col>
            <v-col cols="6">
              <v-btn
                block
                color="primary"
                variant="outlined"
                @click="verifyCredentials"
                :loading="verifying"
              >
                <v-icon class="mr-2">mdi-shield-check</v-icon>
                Verify Room
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions class="pa-6 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="showJoinRoom = false"> Cancel </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="joinRoom"
            :disabled="!canJoin"
            :loading="joining"
          >
            <v-icon class="mr-2">mdi-login</v-icon>
            Join Room
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      location="top center"
      :timeout="4000"
    >
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
      showCreateRoom: false,
      showJoinRoom: false,
      creating: false,
      joining: false,
      verifying: false,
      createForm: {
        roomName: "",
      },
      roomPreview: {
        roomId: "",
        secret: "",
      },
      defaultRoomName: "My Teleprompter Room",
      joinForm: {
        roomId: "",
        secret: "",
      },
      joinErrors: {
        roomId: [],
        secret: [],
      },
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },
    };
  },

  computed: {
    canJoin() {
      return this.joinForm.roomId && this.joinForm.secret && !this.joining;
    },
  },

  mounted() {
    this.defaultRoomName = this.generateDefaultRoomName();
    this.generateRoomPreview();
  },

  watch: {
    showCreateRoom(newVal) {
      if (newVal) {
        this.defaultRoomName = this.generateDefaultRoomName();
        this.generateRoomPreview();
        this.createForm.roomName = this.defaultRoomName;
      }
    },
  },

  methods: {
    generateDefaultRoomName() {
      // Generate a default room name using adjective + animal pattern
      const adjectives = [
        "Amazing",
        "Brilliant",
        "Creative",
        "Dynamic",
        "Elegant",
        "Fantastic",
        "Great",
        "Happy",
        "Incredible",
        "Joyful",
      ];
      const animals = [
        "Lion",
        "Eagle",
        "Tiger",
        "Wolf",
        "Bear",
        "Fox",
        "Hawk",
        "Whale",
        "Dolphin",
        "Shark",
      ];
      const adjective =
        adjectives[Math.floor(Math.random() * adjectives.length)];
      const animal = animals[Math.floor(Math.random() * animals.length)];
      return `${adjective} ${animal}`;
    },

    async generateRoomPreview() {
      // Generate preview credentials for display
      this.roomPreview.roomId = `room-${crypto.randomUUID()}`;
      this.roomPreview.secret = Array.from(
        { length: 48 },
        () =>
          "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"[
            crypto.getRandomValues(new Uint32Array(1))[0] % 70
          ]
      ).join("");
    },

    cancelCreateRoom() {
      this.showCreateRoom = false;
      this.createForm.roomName = "";
      this.roomPreview = { roomId: "", secret: "" };
    },

    async createRoom() {
      this.creating = true;
      try {
        const requestBody = {};
        if (this.createForm.roomName.trim()) {
          requestBody.room_name = this.createForm.roomName.trim();
        }

        const response = await fetch(`${config.getApiUrl()}/api/rooms`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error("Failed to create room");
        }

        const roomData = await response.json();
        this.showSnackbar("Room created successfully!", "success");
        this.showCreateRoom = false;

        // Navigate to controller with room credentials
        this.$router.push({
          path: "/controller",
          query: {
            room: roomData.room_id,
            secret: roomData.secret,
          },
        });
      } catch (error) {
        console.error("Error creating room:", error);
        this.showSnackbar("Failed to create room. Please try again.", "error");
      } finally {
        this.creating = false;
      }
    },

    async verifyCredentials() {
      this.verifying = true;
      this.joinErrors = { roomId: [], secret: [] };

      try {
        const response = await fetch(
          `${config.getApiUrl()}/api/rooms/${this.joinForm.roomId}/verify`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ secret: this.joinForm.secret }),
          }
        );

        const result = await response.json();

        if (result.valid) {
          this.showSnackbar("Room credentials verified!", "success");
        } else {
          this.showSnackbar("Invalid room credentials", "error");
        }
      } catch (error) {
        console.error("Error verifying credentials:", error);
        this.showSnackbar("Failed to verify credentials", "error");
      } finally {
        this.verifying = false;
      }
    },

    async joinRoom() {
      this.joining = true;
      this.joinErrors = { roomId: [], secret: [] };

      // Validate form
      if (!this.joinForm.roomId) {
        this.joinErrors.roomId.push("Room ID is required");
      }
      if (!this.joinForm.secret) {
        this.joinErrors.secret.push("Room secret is required");
      }

      if (this.joinErrors.roomId.length || this.joinErrors.secret.length) {
        this.joining = false;
        return;
      }

      try {
        // Always navigate to teleprompter view since we removed role selection
        this.$router.push({
          path: "/teleprompter",
          query: {
            room: this.joinForm.roomId,
            secret: this.joinForm.secret,
          },
        });
      } catch (error) {
        console.error("Error joining room:", error);
        this.showSnackbar("Failed to join room", "error");
      } finally {
        this.joining = false;
      }
    },

    async pasteCredentials() {
      try {
        const text = await navigator.clipboard.readText();

        // Try to parse as JSON first (for programmatic sharing)
        try {
          const credentials = JSON.parse(text);
          if (credentials.room_id && credentials.secret) {
            this.joinForm.roomId = credentials.room_id;
            this.joinForm.secret = credentials.secret;
            this.showSnackbar("Credentials pasted!", "success");
            return;
          }
        } catch (e) {
          // Not JSON, try other formats
        }

        // Try to extract from URL format
        const urlMatch = text.match(/room=([^&]+)&secret=([^&]+)/);
        if (urlMatch) {
          this.joinForm.roomId = urlMatch[1];
          this.joinForm.secret = urlMatch[2];
          this.showSnackbar("Credentials extracted from URL!", "success");
          return;
        }

        // Try simple space/comma separated format
        const parts = text.trim().split(/[\s,]+/);
        if (parts.length >= 2) {
          this.joinForm.roomId = parts[0];
          this.joinForm.secret = parts[1];
          this.showSnackbar("Credentials pasted!", "success");
          return;
        }

        this.showSnackbar(
          "Could not parse credentials from clipboard",
          "warning"
        );
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
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.greyed-out {
  opacity: 0.7;
}

.greyed-out :deep(.v-field__input) {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
