// Configuration utility for backend URL
export const config = {
  // Get the configuration object
  getConfig() {
    return window.__TELEPROMPTER_CONFIG__ || {}
  },

  // Try to get backend URL from various sources
  getBackendUrl() {
    const teleConfig = this.getConfig()
    
    // 1. Check server-provided backend URL
    if (teleConfig.backendUrl) {
      return teleConfig.backendUrl
    }
    
    // 2. Check for build-time environment variable (fallback)
    if (typeof __BACKEND_URL__ !== 'undefined') {
      return __BACKEND_URL__
    }
    
    // 3. Default to current location with API subpath
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    const host = window.location.host
    const subpath = teleConfig.subpath || ''
    return `${protocol}//${host}${subpath}/api`
  },
  
  // Get API URL for HTTP requests
  getApiUrl() {
    return this.getBackendUrl()
  },
  
  // Get WebSocket URL for the backend
  getWebSocketUrl() {
    const teleConfig = this.getConfig()
    
    // 1. Check server-provided WebSocket URL
    if (teleConfig.wsUrl) {
      return teleConfig.wsUrl
    }
    
    // 2. Derive from backend URL
    const backendUrl = this.getBackendUrl()
    return backendUrl.replace(/^http/, 'ws')
  },

  // Get UI subpath
  getSubpath() {
    const teleConfig = this.getConfig()
    return teleConfig.subpath || ''
  }
}