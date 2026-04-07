/*
Module: 6. User Interface
Author: Forked
Date: 2026-01-27
Purpose: Provides the vite.config module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  envPrefix: "CTRON_",
  test: {
    environment: "jsdom",
    setupFiles: "vitest.setup.ts",
  },
  server: {
    port: 3000,
    host: true, // needed for the Docker Container port mapping to work
  },
});
