import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  base: "/static/django_airavata_auth/dist/",
  build: {
    manifest: "manifest.json",
    outDir: resolve(__dirname, "./static/django_airavata_auth/dist"),
    rollupOptions: {
      input: {
        "user-profile": resolve(
          __dirname,
          "./static/django_airavata_auth/js/entry-user-profile.js"
        ),
      },
    },
  },
  resolve: {
    extensions: [".vue", ".js", ".json"],
    alias: {
      "@": resolve(__dirname, "./static/django_airavata_auth/js"),
    },
  },
  server: {
    port: 9000,
    origin: "http://localhost:9000",
  },
});
