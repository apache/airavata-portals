import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "static/django_airavata_api/js/index.js"),
      name: "AiravataAPI",
      fileName: "airavata-api",
      formats: ["umd"],
    },
    outDir: resolve(__dirname, "static/django_airavata_api/dist"),
  },
});
