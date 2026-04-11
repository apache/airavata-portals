import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  base: "/static/django_airavata_groups/dist/",
  build: {
    manifest: "manifest.json",
    outDir: resolve(__dirname, "./static/django_airavata_groups/dist"),
    rollupOptions: {
      input: {
        "group-list": resolve(
          __dirname,
          "./static/django_airavata_groups/js/group-listing-entry-point.js"
        ),
        "group-create": resolve(
          __dirname,
          "./static/django_airavata_groups/js/group-create-entry-point.js"
        ),
        "group-edit": resolve(
          __dirname,
          "./static/django_airavata_groups/js/group-edit-entry-point.js"
        ),
      },
    },
  },
  resolve: {
    extensions: [".vue", ".js", ".json"],
    alias: {
      "@": resolve(__dirname, "./static/django_airavata_groups/js"),
    },
  },
  server: {
    port: 9000,
    origin: "http://localhost:9000",
  },
});
