import { defineConfig } from "vite";

export default defineConfig({
  clearScreen: false,
  root: "frontend",
  publicDir: "../static",
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/chat": "http://localhost:8000",
      "/history": "http://localhost:8000",
      "/workflows": "http://localhost:8000",
      "/prompts": "http://localhost:8000",
      "/files": "http://localhost:8000",
      "/projects": "http://localhost:8000",
      "/config": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    target: ["es2021", "chrome100"],
    minify: "esbuild",
    sourcemap: false,
  },
});
