import { defineConfig } from "vite";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const PROXY_ROUTES = [
  "/chat", "/history", "/workflows", "/prompts",
  "/files", "/projects", "/config", "/health", "/git", "/auth", "/usage",
  "/work-items", "/entities", "/search", "/billing", "/admin", "/logs",
  "/agent-roles", "/system-roles", "/documents", "/user", "/agents",
  "/graph", "/graph-workflows",
];

export default defineConfig({
  clearScreen: false,
  root: "frontend",
  publicDir: "../static",
  define: {
    // Inject backend URL into the frontend bundle
    "import.meta.env.VITE_BACKEND_URL": JSON.stringify(BACKEND_URL),
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: Object.fromEntries(
      PROXY_ROUTES.map((route) => [route, BACKEND_URL])
    ),
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    target: ["es2021", "chrome100"],
    minify: "esbuild",
    sourcemap: false,
  },
});
