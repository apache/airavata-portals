import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  base: "/static/django_airavata_workspace/dist/",
  build: {
    manifest: "manifest.json",
    outDir: resolve(__dirname, "./static/django_airavata_workspace/dist"),
    rollupOptions: {
      input: {
        dashboard: resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-dashboard.js"
        ),
        "project-list": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-project-list.js"
        ),
        applications: resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-applications.js"
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
        compute: resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-compute.js"
        ),
        datasets: resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-datasets.js"
        ),
        "datasets-list": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-datasets-list.js"
        ),
        credentials: resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-credentials.js"
        ),
        "gateway-settings": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-gateway-settings.js"
        ),
        "storage-detail": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-storage-detail.js"
        ),
        "compute-detail": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-compute-detail.js"
        ),
        "project-overview": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-project-overview.js"
        ),
        "application-editor": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-application-editor.js"
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
    extensions: [".vue", ".js", ".json"],
    alias: {
      "@": resolve(__dirname, "./static/django_airavata_workspace/js"),
    },
  },
  server: {
    port: 9000,
    origin: "http://localhost:9000",
  },
});
