import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // Target backend untuk proxy dev — bisa di-override via VITE_PROXY_TARGET (#17).
  // Pakai 127.0.0.1 (IPv4) eksplisit: hindari 'localhost' yang bisa resolve ke
  // IPv6 (::1) dan nyasar ke container Docker lain yang menempati :8000.
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // Forward /api/* dan /uploads/* ke backend FastAPI saat development
        '/api': { target: proxyTarget, changeOrigin: true },
        '/uploads': { target: proxyTarget, changeOrigin: true },
      },
    },
    build: {
      // Code splitting agar bundle awal lebih ringan (#33)
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            charts: ['recharts'],
            icons: ['lucide-react'],
          },
        },
      },
      chunkSizeWarningLimit: 800,
    },
  }
})
