import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // exceljs (~930 kB) va en un chunk aparte que solo se descarga al exportar.
    chunkSizeWarningLimit: 1000,
  },
  server: {
    port: 5173,
    strictPort: true, // el backend solo admite este origen en CORS
  },
})
