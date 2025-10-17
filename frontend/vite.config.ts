import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
      }
    }
    ,
    // Ensure Vite HMR client has a defined host/port so it doesn't build invalid ws:// URLs
    hmr: {
      host: process.env.VITE_HMR_HOST || 'localhost',
      port: Number(process.env.VITE_HMR_PORT || 5173),
    }
  },
  define: {
    __API_BASE_URL__: JSON.stringify(
      process.env.VITE_API_BASE_URL ||
      'http://localhost:8080'
    )
  }
});
