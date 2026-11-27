// Vite and Vitest configuration for the CreatorIQ React frontend.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // Enable React fast-refresh and JSX compilation.
  plugins: [react()],
  // Run the local development server on port 5173.
  server: { port: 5173 },
  // Configure Vitest to use a browser-like DOM environment and global test helpers.
  test: {
    environment: "jsdom",
    setupFiles: "./src/__tests__/setup.js",
    globals: true,
  },
});
