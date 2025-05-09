import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/tasks': 'http://localhost:8000',
      '/time_sessions': 'http://localhost:8000',
      '/voice': 'http://localhost:8000',   // so /voice/command is sent to FastAPI
    },
  },
})
