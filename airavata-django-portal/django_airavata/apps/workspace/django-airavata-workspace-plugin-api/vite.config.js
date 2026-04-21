import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(import.meta.dirname, "./js");

export default defineAppConfig({
  appLabel: "django-airavata-workspace-plugin-api",
  srcDir,
  entries: resolve(srcDir, "index.js"),
  isLibrary: true,
  overrides: {
    build: {
      lib: {
        entry: resolve(srcDir, "index.js"),
        name: "WorkspacePluginAPI",
        fileName: "index",
        formats: ["es", "cjs"],
      },
      outDir: resolve(import.meta.dirname, "dist"),
      rollupOptions: {
        external: ["django-airavata-api"],
      },
    },
  },
});
