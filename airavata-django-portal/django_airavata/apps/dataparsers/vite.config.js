import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

const publicPath = "/static/django_airavata_dataparsers/dist/";

// Emit a webpack-stats.json compatible with django-webpack-loader so the Django
// templates keep resolving each page's bundle by name (parser-list,
// parser-details, parser-edit) after the Vue CLI/webpack -> Vite migration.
// Entries are ES module bundles, so base.html loads them via
// <script type="module">: the browser then fetches statically-imported JS
// chunks itself, so only the entry script is listed. Extracted CSS is not part
// of the module graph, so we walk the entry's static-import closure and list
// every CSS file (shared chunks' CSS first, the entry's own CSS last, to
// preserve cascade order).
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
  resolve(__dirname, `static/django_airavata_dataparsers/js/${name}`);

export default defineConfig({
  base: publicPath,
  plugins: [vue(), tailwindcss(), djangoWebpackStats()],
  // The source uses extensionless `.vue` imports (Vue CLI resolved them
  // automatically); add `.vue` so Vite/Rollup resolves them too.
  resolve: {
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
    // The shadcn-vue UI components live in the linked common package's source and
    // import each other via `@/lib/utils` / `@/components/ui/*`. This app pulls
    // that source into its bundle (via common's globally-registered UI barrel),
    // so `@` must resolve to common's `js` dir for those imports to load. This
    // app has no `@`-prefixed imports of its own.
    alias: {
      "@": resolve(__dirname, "../../static/common/js"),
    },
    // This package yarn-links django-airavata-common-ui (already migrated to
    // shadcn-vue). reka-ui (shadcn-vue's primitive layer) is provided
    // transitively via the common package; dedupe vue + reka-ui so the linked
    // package and this one share a single copy (otherwise: "Vue is not defined"
    // / invalid-hook errors, and reka-ui relies on module-level singletons).
    dedupe: ["vue", "reka-ui"],
  },
  build: {
    outDir: "static/django_airavata_dataparsers/dist",
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      input: {
        "parser-list": entry("parser-listing-entry-point.js"),
        "parser-details": entry("entry-parser-details.js"),
        "parser-edit": entry("parser-edit-entry-point.js"),
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
