import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3002,
    host: '0.0.0.0'
  },
  build: {
    outDir: 'dist'
  }
})