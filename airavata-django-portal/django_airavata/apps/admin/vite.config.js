import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue2";

const publicPath = "/static/django_airavata_admin/dist/";
const srcDir = resolve(__dirname, "static/django_airavata_admin/src");

// Emit a webpack-stats.json compatible with django-webpack-loader so admin_base.html
// keeps resolving the single-page bundle by name ('app') after the Vue CLI/webpack
// -> Vite migration. The entry is an ES module bundle, so admin_base.html loads it
// via <script type="module">: the browser fetches statically-imported JS chunks
// itself, so only the entry script is listed. Extracted CSS is not part of the
// module graph, so we walk the entry's static-import closure and list every CSS
// file (shared chunks' CSS first, the entry's own CSS last, to preserve cascade).
function djangoWebpackStats() {
  return {
    name: "django-webpack-stats",
    generateBundle(_options, bundle) {
      const chunks = {};
      for (const fileName of Object.keys(bundle)) {
        const item = bundle[fileName];
        if (item.type !== "chunk" || !item.isEntry) continue;
        const css = [];
        const seen = new Set();
        const visited = new Set();
        const walk = (name) => {
          if (visited.has(name)) return;
          visited.add(name);
          const chunk = bundle[name];
          if (!chunk || chunk.type !== "chunk") return;
          for (const imp of chunk.imports || []) walk(imp);
          for (const f of chunk.viteMetadata?.importedCss || []) {
            if (!seen.has(f)) (seen.add(f), css.push(f));
          }
        };
        walk(fileName);
        const files = [fileName, ...css].map((f) => ({
          name: f,
          publicPath: publicPath + f,
        }));
        chunks[item.name] = files;
      }
      this.emitFile({
        type: "asset",
        fileName: "webpack-stats.json",
        source: JSON.stringify({ status: "done", publicPath, chunks }, null, 2),
      });
    },
  };
}

export default defineConfig({
  base: publicPath,
  plugins: [vue(), djangoWebpackStats()],
  resolve: {
    // `@` -> src (Vue CLI default, used by the unit specs); `.vue` so extensionless
    // imports resolve like they did under Vue CLI.
    alias: { "@": srcDir },
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
  },
  build: {
    outDir: "static/django_airavata_admin/dist",
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      input: { app: resolve(srcDir, "main.js") },
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
  test: {
    globals: true,
    environment: "jsdom",
    include: ["static/**/*.spec.js"],
  },
});
