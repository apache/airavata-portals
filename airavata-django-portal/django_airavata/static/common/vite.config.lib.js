import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

// CommonUI UMD library for external custom apps. django-airavata-api is provided
// as the global AiravataAPI (matching the old webpack LIBRARY_MODE externals).
// Runs after the app build with emptyOutDir:false so it adds to ./dist.
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
    alias: {
      "@": resolve(__dirname, "js"),
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: false,
    lib: {
      entry: resolve(__dirname, "js/components.js"),
      name: "CommonUI",
      formats: ["umd"],
      fileName: () => "CommonUI.umd.js",
    },
    rollupOptions: {
      external: ["django-airavata-api"],
      output: { globals: { "django-airavata-api": "AiravataAPI" } },
    },
  },
});
