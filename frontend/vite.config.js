import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'VITE_');
  return {
    plugins: [react()],
    resolve: {
        alias: {
            '@': new URL('./src', import.meta.url).pathname,
        },
    },
    server: {
        port: 5173,
        host: true,
        proxy: {
            '/api': {
                target: env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        outDir: 'dist',
        sourcemap: true,
    },
  };
});
