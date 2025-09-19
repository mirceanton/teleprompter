// Configuration utility for backend URL
class TeleprompterConfig {
  constructor() {
    this._config = null
    this._loadPromise = null
  }

  // Load configuration from config.json file
  async loadConfig() {
    if (this._loadPromise) {
      return this._loadPromise
    }

    this._loadPromise = this._fetchConfig()
    return this._loadPromise
  }

  async _fetchConfig() {
    try {
      const response = await fetch('/config.json')
      if (response.ok) {
        this._config = await response.json()
        console.log('Loaded runtime configuration from config.json:', this._config)
      } else {
        console.warn('Could not load config.json, using defaults')
        this._config = {}
      }
    } catch (error) {
      console.warn('Error loading config.json, using defaults:', error)
      this._config = {}
    }
  }

  // Get backend URL from config.json or default
  getBackendUrl() {
    // Check runtime config loaded from config.json
    if (this._config && this._config.backendUrl) {
      return this._config.backendUrl
    }
    
    // Default to same host with backend port
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    const host = window.location.hostname
    return `${protocol}//${host}:8001`
  }
  
  // Get API URL for HTTP requests
  getApiUrl() {
    return this.getBackendUrl()
  }
  
  // Get WebSocket URL for the backend
  getWebSocketUrl() {
    const backendUrl = this.getBackendUrl()
    // Convert HTTP/HTTPS to WS/WSS
    return backendUrl.replace(/^http/, 'ws')
  }
}

// Create and export singleton instance
export const config = new TeleprompterConfig()