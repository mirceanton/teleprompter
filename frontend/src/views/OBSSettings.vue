<template>
  <v-app theme="dark">
    <v-app-bar app elevation="16" height="64" color="grey-darken-4">
      <v-container fluid class="d-flex align-center">
        <v-btn icon variant="text" @click="goBack" class="mr-2">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <div class="d-flex align-center">
          <v-icon color="teal" size="32" class="mr-3">mdi-cog</v-icon>
          <div class="text-h5 font-weight-bold">OBS Settings</div>
        </div>
      </v-container>
    </v-app-bar>

    <v-main>
      <v-container class="py-8">
        <v-row justify="center">
          <v-col cols="12" md="8" lg="6">
            <v-card class="pa-6">
              <v-card-title class="text-h5 mb-4">
                OBS Integration Settings
              </v-card-title>
              <v-card-subtitle class="mb-6">
                Configure connection to OBS Studio for automated recording
                control
              </v-card-subtitle>

              <v-form @submit.prevent="saveSettings">
                <!-- Enable/Disable Toggle -->
                <v-switch
                  v-model="settings.enabled"
                  label="Enable OBS Integration"
                  color="teal"
                  hide-details
                  class="mb-6"
                ></v-switch>

                <v-divider class="mb-6"></v-divider>

                <!-- Connection Settings -->
                <div class="mb-4">
                  <h3 class="text-subtitle-1 mb-4 font-weight-bold">
                    Connection Settings
                  </h3>

                  <v-text-field
                    v-model="settings.host"
                    label="OBS Host"
                    placeholder="localhost"
                    variant="outlined"
                    :disabled="!settings.enabled"
                    class="mb-4"
                    hint="Hostname or IP address of the computer running OBS"
                    persistent-hint
                  ></v-text-field>

                  <v-text-field
                    v-model.number="settings.port"
                    label="WebSocket Port"
                    placeholder="4455"
                    variant="outlined"
                    type="number"
                    :disabled="!settings.enabled"
                    class="mb-4"
                    hint="WebSocket port configured in OBS (default: 4455)"
                    persistent-hint
                  ></v-text-field>

                  <v-text-field
                    v-model="settings.password"
                    label="WebSocket Password"
                    placeholder="Optional"
                    variant="outlined"
                    :type="showPassword ? 'text' : 'password'"
                    :disabled="!settings.enabled"
                    class="mb-4"
                    hint="Leave empty if no password is set in OBS"
                    persistent-hint
                  >
                    <template v-slot:append-inner>
                      <v-icon
                        @click="showPassword = !showPassword"
                        style="cursor: pointer"
                      >
                        {{ showPassword ? "mdi-eye-off" : "mdi-eye" }}
                      </v-icon>
                    </template>
                  </v-text-field>
                </div>

                <v-divider class="mb-6"></v-divider>

                <!-- Recording Settings -->
                <div class="mb-6">
                  <h3 class="text-subtitle-1 mb-4 font-weight-bold">
                    Recording Settings
                  </h3>

                  <v-text-field
                    v-model.number="settings.start_delay"
                    label="Start Delay (seconds)"
                    placeholder="0"
                    variant="outlined"
                    type="number"
                    min="0"
                    max="60"
                    :disabled="!settings.enabled"
                    hint="Delay before starting the teleprompter after OBS recording starts"
                    persistent-hint
                  ></v-text-field>
                </div>

                <!-- Connection Status -->
                <v-alert
                  v-if="connectionStatus"
                  :type="connectionStatus.type"
                  :title="connectionStatus.title"
                  class="mb-6"
                >
                  {{ connectionStatus.message }}
                </v-alert>

                <!-- Action Buttons -->
                <div class="d-flex gap-3">
                  <v-btn
                    color="teal"
                    variant="outlined"
                    @click="testConnection"
                    :disabled="!settings.enabled || testing"
                    :loading="testing"
                    prepend-icon="mdi-lan-connect"
                  >
                    Test Connection
                  </v-btn>

                  <v-spacer></v-spacer>

                  <v-btn variant="outlined" @click="goBack"> Cancel </v-btn>

                  <v-btn
                    color="teal"
                    variant="flat"
                    type="submit"
                    :loading="saving"
                    prepend-icon="mdi-content-save"
                  >
                    Save Settings
                  </v-btn>
                </div>
              </v-form>
            </v-card>

            <!-- Help Card -->
            <v-card class="mt-6 pa-6">
              <v-card-title class="text-h6 mb-4">
                <v-icon class="mr-2" color="info">mdi-information</v-icon>
                How to Enable OBS WebSocket
              </v-card-title>

              <v-card-text>
                <ol class="pl-4">
                  <li class="mb-2">
                    Open OBS Studio and go to
                    <strong>Tools → WebSocket Server Settings</strong>
                  </li>
                  <li class="mb-2">
                    Check <strong>"Enable WebSocket server"</strong>
                  </li>
                  <li class="mb-2">
                    Note the <strong>Server Port</strong> (default: 4455)
                  </li>
                  <li class="mb-2">
                    Optionally set a password for security
                  </li>
                  <li class="mb-2">
                    Click <strong>Apply</strong> and <strong>OK</strong>
                  </li>
                  <li class="mb-2">
                    Enter the same settings here and click
                    <strong>Test Connection</strong>
                  </li>
                </ol>

                <v-alert type="info" variant="tonal" class="mt-4">
                  <strong>Note:</strong> Make sure OBS is running on the
                  specified host before testing the connection.
                </v-alert>
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
  name: "OBSSettings",

  data() {
    return {
      settings: {
        host: "localhost",
        port: 4455,
        password: "",
        enabled: false,
        start_delay: 0,
      },
      showPassword: false,
      connectionStatus: null,
      testing: false,
      saving: false,
      snackbar: {
        show: false,
        text: "",
        color: "success",
      },
    };
  },

  async mounted() {
    await this.loadSettings();
  },

  methods: {
    goBack() {
      this.$router.back();
    },

    async loadSettings() {
      try {
        const apiUrl = config.getApiUrl();
        const response = await fetch(`${apiUrl}/api/obs/status`);

        if (response.ok) {
          const data = await response.json();
          this.settings = {
            host: data.host,
            port: data.port,
            password: "",
            enabled: data.enabled,
            start_delay: data.start_delay,
          };

          if (data.connected) {
            this.connectionStatus = {
              type: "success",
              title: "Connected",
              message: `Successfully connected to OBS at ${data.host}:${data.port}`,
            };
          }
        }
      } catch (error) {
        console.error("Failed to load OBS settings:", error);
        this.showSnackbar("Failed to load OBS settings", "error");
      }
    },

    async testConnection() {
      this.testing = true;
      this.connectionStatus = null;

      try {
        const apiUrl = config.getApiUrl();
        const response = await fetch(`${apiUrl}/api/obs/test-connection`, {
          method: "POST",
        });

        const data = await response.json();

        if (data.success) {
          this.connectionStatus = {
            type: "success",
            title: "Connection Successful",
            message: data.message,
          };
          this.showSnackbar("Successfully connected to OBS", "success");
        } else {
          this.connectionStatus = {
            type: "error",
            title: "Connection Failed",
            message: data.message,
          };
          this.showSnackbar("Failed to connect to OBS", "error");
        }
      } catch (error) {
        console.error("Failed to test OBS connection:", error);
        this.connectionStatus = {
          type: "error",
          title: "Connection Failed",
          message: "Failed to connect to backend server",
        };
        this.showSnackbar("Failed to test connection", "error");
      } finally {
        this.testing = false;
      }
    },

    async saveSettings() {
      this.saving = true;
      this.connectionStatus = null;

      try {
        const apiUrl = config.getApiUrl();
        const response = await fetch(`${apiUrl}/api/obs/config`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(this.settings),
        });

        const data = await response.json();

        if (data.success) {
          this.showSnackbar("OBS settings saved successfully", "success");
          this.connectionStatus = {
            type: "success",
            title: "Settings Saved",
            message: data.message,
          };

          // Reload settings to get updated connection status
          setTimeout(() => {
            this.loadSettings();
          }, 1000);
        } else {
          this.showSnackbar(data.message, "warning");
          this.connectionStatus = {
            type: "warning",
            title: "Partial Success",
            message: data.message,
          };
        }
      } catch (error) {
        console.error("Failed to save OBS settings:", error);
        this.showSnackbar("Failed to save OBS settings", "error");
        this.connectionStatus = {
          type: "error",
          title: "Save Failed",
          message: "Failed to communicate with backend server",
        };
      } finally {
        this.saving = false;
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
.v-card {
  border-radius: 12px;
}

ol li {
  line-height: 1.8;
}
</style>
