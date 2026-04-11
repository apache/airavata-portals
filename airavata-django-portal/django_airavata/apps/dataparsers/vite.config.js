import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  base: "/static/django_airavata_dataparsers/dist/",
  build: {
    manifest: "manifest.json",
    outDir: resolve(__dirname, "./static/django_airavata_dataparsers/dist"),
    rollupOptions: {
      input: {
        "parser-details": resolve(
          __dirname,
          "./static/django_airavata_dataparsers/js/entry-parser-details.js"
        ),
        "parser-list": resolve(
          __dirname,
          "./static/django_airavata_dataparsers/js/parser-listing-entry-point.js"
        ),
        "parser-edit": resolve(
          __dirname,
          "./static/django_airavata_dataparsers/js/parser-edit-entry-point.js"
        ),
      },
    },
  },
  resolve: {
    extensions: [".vue", ".js", ".json"],
    alias: {
      "@": resolve(__dirname, "./static/django_airavata_dataparsers/js"),
    },
  },
  server: {
    port: 9000,
    origin: "http://localhost:9000",
  },
});
