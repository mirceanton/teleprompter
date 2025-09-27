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
                  Choose your mode to get started with the teleprompter.
                </p>

                <v-row class="mb-4">
                  <!-- Controller Mode -->
                  <v-col cols="12" md="6">
                    <v-btn
                      block
                      color="primary"
                      size="x-large"
                      class="pa-8"
                      style="min-height: 120px;"
                      @click="startControllerMode"
                      :loading="loading"
                      :disabled="loading"
                    >
                      <div class="text-center">
                        <v-icon size="48" class="mb-3">mdi-laptop</v-icon>
                        <div class="text-h6 mb-2">💻 Controller Mode</div>
                        <div class="text-body-2">
                          Control teleprompter playback and edit scripts
                        </div>
                      </div>
                    </v-btn>
                  </v-col>

                  <!-- Teleprompter Mode -->
                  <v-col cols="12" md="6">
                    <v-btn
                      block
                      color="success"
                      size="x-large"
                      class="pa-8"
                      style="min-height: 120px;"
                      @click="startTeleprompterMode"
                      :loading="loading"
                      :disabled="loading"
                    >
                      <div class="text-center">
                        <v-icon size="48" class="mb-3">mdi-monitor</v-icon>
                        <div class="text-h6 mb-2">📱 Teleprompter Mode</div>
                        <div class="text-body-2">
                          Display teleprompter text for reading
                        </div>
                      </div>
                    </v-btn>
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
      loading: false,
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },
    };
  },

  methods: {
    async startControllerMode() {
      this.loading = true;
      try {
        const apiUrl = config.getApiUrl();
        
        // Join as controller (simplified API)
        const response = await fetch(`${apiUrl}/api/join`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            role: "controller",
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to join as controller");
        }

        const joinData = await response.json();

        if (!joinData.success) {
          this.showSnackbar(joinData.message, "error");
          return;
        }

        // Store minimal credentials in session storage
        sessionStorage.setItem(
          "teleprompter_credentials",
          JSON.stringify({
            role: "controller",
          })
        );

        // Navigate to controller
        this.$router.push({
          path: "/controller",
          query: {
            role: "controller",
          },
        });
      } catch (error) {
        console.error("Error starting controller mode:", error);
        this.showSnackbar("Failed to start controller mode. Please try again.", "error");
      } finally {
        this.loading = false;
      }
    },

    async startTeleprompterMode() {
      this.loading = true;
      try {
        const apiUrl = config.getApiUrl();
        
        // Join as teleprompter (simplified API)
        const response = await fetch(`${apiUrl}/api/join`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            role: "teleprompter",
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to join as teleprompter");
        }

        const joinData = await response.json();

        if (!joinData.success) {
          this.showSnackbar(joinData.message, "error");
          return;
        }

        // Store minimal credentials in session storage
        sessionStorage.setItem(
          "teleprompter_credentials",
          JSON.stringify({
            role: "teleprompter",
          })
        );

        // Navigate to teleprompter
        this.$router.push({
          path: "/teleprompter",
          query: {
            role: "teleprompter",
          },
        });
      } catch (error) {
        console.error("Error starting teleprompter mode:", error);
        this.showSnackbar("Failed to start teleprompter mode. Please try again.", "error");
      } finally {
        this.loading = false;
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
.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
