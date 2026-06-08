import { resolve } from "node:path";
import { defineConfig } from "vite";

// Builds the standalone UMD bundle (window.AiravataAPI) consumed by external
// custom apps. Internal consumers import the source directly via the package
// "main"/"module" entry (./static/django_airavata_api/js/index.js).
export default defineConfig({
  build: {
    outDir: "static/django_airavata_api/dist",
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "static/django_airavata_api/js/index.js"),
      name: "AiravataAPI",
      formats: ["umd"],
      fileName: () => "airavata-api.js",
    },
  },
  test: {
    // jest-compatible globals (test/expect/describe) for the existing specs;
    // jsdom provides the `window` that index.js touches at import time.
    globals: true,
    environment: "jsdom",
    include: ["static/**/*.test.js"],
  },
});
