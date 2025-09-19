<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title> 📱 Remote Teleprompter </v-toolbar-title>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height">
        <v-row justify="center" align="center" class="fill-height">
          <v-col cols="12" md="8" lg="6">
            <!-- Room Setup Card -->
            <v-card elevation="8">
              <v-card-title class="text-h5 pa-6">
                <v-icon class="mr-2">mdi-account-group</v-icon>
                Join or Create a Room
              </v-card-title>

              <v-card-text class="pa-6">
                <v-text-field
                  v-model="channelName"
                  label="Room ID"
                  placeholder="Enter room ID or leave blank to generate one"
                  prepend-icon="mdi-key"
                  variant="outlined"
                  class="mb-4"
                  @keypress.enter="handleJoin"
                />

                <v-row class="mb-4">
                  <v-col cols="6">
                    <v-btn
                      block
                      color="secondary"
                      variant="outlined"
                      size="large"
                      @click="generateRoomId"
                    >
                      <v-icon class="mr-2">mdi-dice-6</v-icon>
                      Generate Room ID
                    </v-btn>
                  </v-col>
                  <v-col cols="6">
                    <v-btn
                      block
                      color="primary"
                      variant="outlined"
                      size="large"
                      @click="pasteRoomId"
                    >
                      <v-icon class="mr-2">mdi-content-paste</v-icon>
                      Paste Room ID
                    </v-btn>
                  </v-col>
                </v-row>

                <v-divider class="my-4" />

                <h3 class="text-h6 mb-4">Select Your Role:</h3>

                <v-row>
                  <v-col cols="12" md="6">
                    <v-card
                      class="role-card"
                      :class="{ selected: selectedRole === 'controller' }"
                      @click="selectedRole = 'controller'"
                      elevation="2"
                      hover
                    >
                      <v-card-text class="text-center pa-6">
                        <v-icon size="48" color="primary" class="mb-2"
                          >mdi-laptop</v-icon
                        >
                        <h4 class="text-h6 mb-2">💻 Controller</h4>
                        <p class="text-body-2">
                          Edit scripts and control playback from your computer
                        </p>
                      </v-card-text>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-card
                      class="role-card"
                      :class="{ selected: selectedRole === 'teleprompter' }"
                      @click="selectedRole = 'teleprompter'"
                      elevation="2"
                      hover
                    >
                      <v-card-text class="text-center pa-6">
                        <v-icon size="48" color="primary" class="mb-2"
                          >mdi-cellphone</v-icon
                        >
                        <h4 class="text-h6 mb-2">📱 Teleprompter</h4>
                        <p class="text-body-2">
                          Display scrolling text on your phone or tablet
                        </p>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>

                <v-btn
                  block
                  color="primary"
                  size="x-large"
                  class="mt-6"
                  @click="handleJoin"
                  :disabled="!channelName || !selectedRole"
                >
                  <v-icon class="mr-2">mdi-login</v-icon>
                  Join Room
                </v-btn>
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
export default {
  name: "Landing",
  data() {
    return {
      channelName: "",
      selectedRole: "",
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },
    };
  },

  mounted() {
    // Generate initial room ID
    this.generateRoomId();
  },

  methods: {
    generateRoomId() {
      this.channelName = "room-" + Math.random().toString(36).substring(2, 8);
      this.showSnackbar("New room ID generated!", "success");
    },

    async pasteRoomId() {
      try {
        const text = await navigator.clipboard.readText();
        if (text.trim()) {
          this.channelName = text.trim();
          this.showSnackbar("Room ID pasted!", "success");
        }
      } catch (err) {
        this.showSnackbar(
          "Could not access clipboard. Please paste manually.",
          "warning"
        );
      }
    },

    handleJoin() {
      if (!this.channelName || !this.selectedRole) {
        this.showSnackbar("Please enter a room ID and select a role.", "error");
        return;
      }

      // Navigate using Vue Router instead of window.location.href
      if (this.selectedRole === "controller") {
        this.$router.push({
          path: "/controller",
          query: { room: this.channelName },
        });
      } else {
        this.$router.push({
          path: "/teleprompter",
          query: { room: this.channelName },
        });
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
.role-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.role-card:hover {
  transform: translateY(-2px);
}

.role-card.selected {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
