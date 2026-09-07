import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend (FastAPI) is expected to run on http://localhost:8000.
// Routes are mounted at the root (e.g. /chat, /tasks, /models, /knowledge,
// /files, /health) rather than under an /api prefix, so each of those
// prefixes is proxied individually. This avoids needing CORS middleware
// on the backend during local development.
const BACKEND_URL = 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': BACKEND_URL,
      '/tasks': BACKEND_URL,
      '/models': BACKEND_URL,
      '/knowledge': BACKEND_URL,
      '/files': BACKEND_URL,
      '/health': BACKEND_URL,
      '/artifacts': BACKEND_URL,
      '/audit': BACKEND_URL,
    },
  },
})
