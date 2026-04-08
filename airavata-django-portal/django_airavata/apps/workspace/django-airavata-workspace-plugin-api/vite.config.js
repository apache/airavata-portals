import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  build: {
    lib: {
      entry: resolve(__dirname, "js/index.js"),
      name: "WorkspacePluginAPI",
      fileName: "index",
      formats: ["es", "cjs"],
    },
    outDir: resolve(__dirname, "dist"),
    rollupOptions: {
      external: ["django-airavata-api"],
    },
  },
});
