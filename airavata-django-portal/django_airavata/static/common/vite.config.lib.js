import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue2";

// CommonUI UMD library for external custom apps. django-airavata-api is provided
// as the global AiravataAPI (matching the old webpack LIBRARY_MODE externals).
// Runs after the app build with emptyOutDir:false so it adds to ./dist.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
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
