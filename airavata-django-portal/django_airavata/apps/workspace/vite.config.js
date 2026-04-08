import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  build: {
    manifest: "manifest.json",
    outDir: resolve(__dirname, "./static/django_airavata_workspace/dist"),
    rollupOptions: {
      input: {
        "project-list": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-project-list.js"
        ),
        dashboard: resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-dashboard.js"
        ),
        "create-experiment": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-create-experiment.js"
        ),
        "view-experiment": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-view-experiment.js"
        ),
        "experiment-list": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-experiment-list.js"
        ),
        "edit-experiment": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-edit-experiment.js"
        ),
        "edit-project": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-edit-project.js"
        ),
        "user-storage": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-user-storage.js"
        ),
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        quietDeps: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./static/django_airavata_workspace/js"),
    },
  },
  server: {
    port: 9000,
    origin: "http://localhost:9000",
  },
});
