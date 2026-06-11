import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue2";

const publicPath = "/static/django_airavata_auth/dist/";

// Emit a webpack-stats.json compatible with django-webpack-loader so base.html
// keeps resolving the page bundle by name ('user-profile') after the Vue
// CLI/webpack -> Vite migration. The entry is an ES module bundle, so base.html
// loads it via <script type="module">: the browser fetches statically-imported
// JS chunks itself, so only the entry script is listed. Extracted CSS is not part
// of the module graph, so we walk the entry's static-import closure and list every
// CSS file (shared chunks' CSS first, the entry's own CSS last, to preserve cascade).
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
  // The source uses extensionless `.vue` imports (Vue CLI resolved them
  // automatically); add `.vue` so Vite/Rollup resolves them too.
  resolve: {
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
  },
  build: {
    outDir: "static/django_airavata_auth/dist",
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      // Login/account self-service is hosted by Keycloak now, so this app has
      // no page bundles. The previous "user-profile" entry was removed with the
      // Vue profile editor; add an entry here if a page bundle is reintroduced.
      input: {},
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
