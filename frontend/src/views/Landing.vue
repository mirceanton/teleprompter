<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>Remote Teleprompter</v-toolbar-title>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height">
        <v-row justify="center" align="center" class="fill-height">
          <v-col cols="12" md="10" lg="8">
            <!-- Header Section -->
            <div class="text-center mb-8">
              <v-icon size="64" color="primary" class="mb-4"
                >mdi-presentation-play</v-icon
              >
              <h1 class="text-h3 font-weight-bold mb-3">Remote Teleprompter</h1>
            </div>

            <!-- Mode Selection Cards -->
            <v-row class="mb-4" justify="center">
              <!-- Controller Mode Card -->
              <v-col cols="12" sm="6" md="5">
                <v-card
                  class="mode-card controller-card"
                  :class="{ 'card-loading': loading }"
                  elevation="8"
                  @click="startControllerMode"
                  :disabled="loading"
                >
                  <v-card-text class="pa-8 text-center">
                    <div class="mode-icon-container mb-4">
                      <v-icon size="80" class="mode-icon">mdi-laptop</v-icon>
                    </div>

                    <div class="mode-title mb-3">
                      <h2 class="text-h4 font-weight-bold">Controller</h2>
                      <div
                        class="mode-subtitle text-h6 text-medium-emphasis mt-1"
                      >
                        Command Center
                      </div>
                    </div>
                  </v-card-text>

                  <v-overlay v-if="loading" contained class="loading-overlay">
                    <v-progress-circular
                      indeterminate
                      size="32"
                    ></v-progress-circular>
                  </v-overlay>
                </v-card>
              </v-col>

              <!-- Teleprompter Mode Card -->
              <v-col cols="12" sm="6" md="5">
                <v-card
                  class="mode-card teleprompter-card"
                  :class="{ 'card-loading': loading }"
                  elevation="8"
                  @click="startTeleprompterMode"
                  :disabled="loading"
                >
                  <v-card-text class="pa-8 text-center">
                    <div class="mode-icon-container mb-4">
                      <v-icon size="80" class="mode-icon">mdi-monitor</v-icon>
                    </div>

                    <div class="mode-title mb-3">
                      <h2 class="text-h4 font-weight-bold">Teleprompter</h2>
                      <div
                        class="mode-subtitle text-h6 text-medium-emphasis mt-1"
                      >
                        Display Screen
                      </div>
                    </div>
                  </v-card-text>

                  <v-overlay v-if="loading" contained class="loading-overlay">
                    <v-progress-circular
                      indeterminate
                      size="32"
                    ></v-progress-circular>
                  </v-overlay>
                </v-card>
              </v-col>
            </v-row>

            <!-- Instructions -->
            <div class="text-center mt-8">
              <p class="text-body-1 text-medium-emphasis">
                Select your mode to begin using the teleprompter system
              </p>
            </div>
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
        this.showSnackbar(
          "Failed to start controller mode. Please try again.",
          "error"
        );
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
        this.showSnackbar(
          "Failed to start teleprompter mode. Please try again.",
          "error"
        );
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

.mode-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border-radius: 16px !important;
  position: relative;
  overflow: hidden;
}

.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
}

.mode-card:active {
  transform: translateY(-2px);
}

.controller-card {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  color: white;
}

.controller-card:hover {
  background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%);
}

.teleprompter-card {
  background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%);
  color: white;
}

.teleprompter-card:hover {
  background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
}

.mode-icon-container {
  position: relative;
}

.mode-icon {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 16px;
  backdrop-filter: blur(10px);
}

.mode-title h2 {
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.mode-subtitle {
  opacity: 0.9;
  font-weight: 500;
}

.card-loading {
  pointer-events: none;
  opacity: 0.7;
}

.loading-overlay {
  background: rgba(0, 0, 0, 0.2) !important;
  backdrop-filter: blur(2px);
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .mode-card {
    margin-bottom: 16px;
  }

  .mode-icon {
    padding: 12px;
  }

  .mode-title h2 {
    font-size: 1.5rem !important;
  }
}

/* Dark theme support */
.v-theme--dark .mode-card {
  border: 1px solid rgba(255, 255, 255, 0.12);
}

/* Animation for card entrance */
.mode-card {
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Stagger animation for second card */
.v-col:nth-child(2) .mode-card {
  animation-delay: 0.1s;
}
</style>
