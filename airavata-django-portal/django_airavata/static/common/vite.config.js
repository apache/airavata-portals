import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

const publicPath = "/static/common/dist/";

// Emit a webpack-stats.json compatible with django-webpack-loader so the Django
// templates' {% render_bundle/get_files 'app'/'shell' ... 'COMMON' %} tags keep
// working unchanged after the webpack -> Vite migration.
function djangoWebpackStats() {
  return {
    name: "django-webpack-stats",
    generateBundle(_options, bundle) {
      // Index emitted CSS assets by their base name (e.g. "css/app.css" -> "app").
      // A CSS-only entry (main.js imports only app.css, no JS) leaves the CSS out
      // of the chunk's viteMetadata.importedCss, so we also match CSS assets to
      // their entry by name.
      const cssByName = {};
      for (const [fileName, item] of Object.entries(bundle)) {
        if (item.type === "asset" && fileName.endsWith(".css")) {
          const base = fileName.split("/").pop().replace(/\.css$/, "");
          (cssByName[base] ||= []).push(fileName);
        }
      }
      const chunks = {};
      for (const fileName of Object.keys(bundle)) {
        const item = bundle[fileName];
        if (item.type === "chunk" && item.isEntry) {
          const files = (chunks[item.name] ||= []);
          const seen = new Set();
          const add = (f) => {
            if (seen.has(f)) return;
            seen.add(f);
            files.push({ name: f, publicPath: publicPath + f });
          };
          add(fileName);
          for (const css of item.viteMetadata?.importedCss || []) add(css);
          for (const css of cssByName[item.name] || []) add(css);
        }
      }
      this.emitFile({
        type: "asset",
        fileName: "webpack-stats.json",
        source: JSON.stringify({ status: "done", publicPath, chunks }, null, 2),
      });
    },
  };
}

// Bundles loaded directly by Django templates (no index.html); entry JS + CSS
// are mapped into webpack-stats.json for django-webpack-loader.
export default defineConfig({
  base: publicPath,
  plugins: [vue(), tailwindcss(), djangoWebpackStats()],
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
