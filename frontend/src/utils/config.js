// Configuration utility for backend URL
export const config = {
  // Try to get backend URL from various sources
  getBackendUrl() {
    // 1. Check if there's a runtime config from window (for Docker env injection)
    if (window.__TELEPROMPTER_CONFIG__ && window.__TELEPROMPTER_CONFIG__.backendUrl) {
      return window.__TELEPROMPTER_CONFIG__.backendUrl
    }
    
    // 2. Check for build-time environment variable
    if (typeof __BACKEND_URL__ !== 'undefined') {
      return __BACKEND_URL__
    }
    
    // 3. Default to same host with backend port
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    const host = window.location.hostname
    return `${protocol}//${host}:8001`
  },
  
  // Get API URL for HTTP requests
  getApiUrl() {
    return this.getBackendUrl()
  },
  
  // Get WebSocket URL for the backend
  getWebSocketUrl() {
    const backendUrl = this.getBackendUrl()
    // Convert HTTP/HTTPS to WS/WSS
    return backendUrl.replace(/^http/, 'ws')
  }
}