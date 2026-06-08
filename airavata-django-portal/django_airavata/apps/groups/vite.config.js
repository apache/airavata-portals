import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue2";

const publicPath = "/static/django_airavata_groups/dist/";

// Emit a webpack-stats.json compatible with django-webpack-loader so the Django
// templates keep resolving each page's bundle by name (group-list, group-create,
// group-edit) after the Vue CLI/webpack -> Vite migration. Entries are ES module
// bundles, so base.html loads them via <script type="module">: the browser then
// fetches statically-imported JS chunks itself, so only the entry script is
// listed. Extracted CSS is not part of the module graph, so we walk the entry's
// static-import closure and list every CSS file (shared chunks' CSS first, the
// entry's own CSS last, to preserve cascade order).
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

const entry = (name) =>
  resolve(__dirname, `static/django_airavata_groups/js/${name}`);

export default defineConfig({
  base: publicPath,
  plugins: [vue(), djangoWebpackStats()],
  // The source uses extensionless `.vue` imports (Vue CLI resolved them
  // automatically); add `.vue` so Vite/Rollup resolves them too.
  resolve: {
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
  },
  build: {
    outDir: "static/django_airavata_groups/dist",
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      input: {
        "group-list": entry("group-listing-entry-point.js"),
        "group-create": entry("group-create-entry-point.js"),
        "group-edit": entry("group-edit-entry-point.js"),
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
