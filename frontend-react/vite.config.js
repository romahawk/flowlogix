import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
      "/login": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
      "/stock_order": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
      "/deliver_direct": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
    },
  },
});