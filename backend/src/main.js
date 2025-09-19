import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import App from './App.vue'

// Import views
import Landing from './views/Landing.vue'
import Controller from './views/Controller.vue'
import Teleprompter from './views/Teleprompter.vue'

// Get base path from configuration
const getBasePath = () => {
  const config = window.__TELEPROMPTER_CONFIG__ || {}
  return config.subpath || ''
}

// Create router
const router = createRouter({
  history: createWebHistory(getBasePath()),
  routes: [
    {
      path: '/',
      name: 'Landing',
      component: Landing
    },
    {
      path: '/controller',
      name: 'Controller',
      component: Controller
    },
    {
      path: '/teleprompter',
      name: 'Teleprompter',
      component: Teleprompter
    }
  ]
})

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark'
  }
})

// Create and mount app
createApp(App)
  .use(router)
  .use(vuetify)
  .mount('#app')