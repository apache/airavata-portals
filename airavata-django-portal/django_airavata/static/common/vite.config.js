import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  base: "/static/common/dist/",
  build: {
    manifest: "manifest.json",
    outDir: resolve(__dirname, "./dist"),
    rollupOptions: {
      input: {
        app: resolve(__dirname, "./js/main.js"),
        cms: resolve(__dirname, "./js/cms.js"),
        notices: resolve(__dirname, "./js/notices.js"),
      },
    },
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./js"),
    },
    extensions: [".mjs", ".js", ".ts", ".jsx", ".tsx", ".json", ".vue"],
  },
});
