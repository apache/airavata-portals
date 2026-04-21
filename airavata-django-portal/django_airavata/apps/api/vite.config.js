import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(import.meta.dirname, "./static/django_airavata_api/js");

export default defineAppConfig({
  appLabel: "django_airavata_api",
  srcDir,
  entries: resolve(srcDir, "index.js"),
  isLibrary: true,
  overrides: {
    build: {
      lib: {
        entry: resolve(srcDir, "index.js"),
        name: "AiravataAPI",
        fileName: "airavata-api",
        formats: ["umd"],
      },
      outDir: resolve(import.meta.dirname, "static/django_airavata_api/dist"),
    },
  },
});
