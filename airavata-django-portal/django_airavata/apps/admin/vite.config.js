import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  build: {
    manifest: "manifest.json",
    outDir: resolve(__dirname, "./static/django_airavata_admin/dist"),
    rollupOptions: {
      input: resolve(
        __dirname,
        "./static/django_airavata_admin/src/main.js"
      ),
    },
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./static/django_airavata_admin/src"),
    },
  },
  server: {
    port: 9000,
    origin: "http://localhost:9000",
  },
});
