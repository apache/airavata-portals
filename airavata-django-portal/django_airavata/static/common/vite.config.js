import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

const publicPath = "/static/common/dist/";

// Bundles loaded directly by Django templates (no index.html); the entry JS +
// CSS are resolved from Vite's native manifest (dist/.vite/manifest.json) by the
// {% vite_js/vite_css %} Django template tags.
export default defineConfig({
  base: publicPath,
  plugins: [vue(), tailwindcss()],
  // The source uses extensionless `.vue` imports throughout (Vue CLI resolved
  // them automatically); add `.vue` so Vite/Rollup resolves them too.
  resolve: {
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
    alias: {
      "@": resolve(__dirname, "js"),
    },
  },
  build: {
    outDir: "dist",
    manifest: true,
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      input: {
        app: resolve(__dirname, "js/main.js"),
        shell: resolve(__dirname, "js/shell.js"),
      },
      output: {
        entryFileNames: "js/[name].js",
        chunkFileNames: "js/[name].js",
        assetFileNames: (info) => {
          const name = info.names?.[0] ?? info.name ?? "";
          return name.endsWith(".css") ? "css/[name][extname]" : "assets/[name][extname]";
        },
      },
    },
  },
});
