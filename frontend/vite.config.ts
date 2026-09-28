import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  // Reads the single .env file at the repo root (one env file for the whole project).
  envDir: path.resolve(__dirname, ".."),
  server: {
    port: 5173,
  },
});
