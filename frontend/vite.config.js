import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
    // Only our own tests — without this, vitest walks node_modules too.
    include: ["src/**/*.test.{js,jsx}"],
  },
});
