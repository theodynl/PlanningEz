import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development the Vite dev server proxies API calls to the FastAPI
// backend on :8000. In production the built assets are served by FastAPI.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "dist",
  },
});
