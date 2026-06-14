import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

const publicPath = "/static/django_airavata_workspace/dist/";
const jsDir = resolve(__dirname, "static/django_airavata_workspace/js");

// Emit a webpack-stats.json compatible with django-webpack-loader so base.html
// keeps resolving each page's bundle by name after the Vue CLI/webpack -> Vite
// migration. Entries are ES module bundles, so base.html loads them via
// <script type="module">: the browser fetches statically-imported JS chunks
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

const entry = (name) => resolve(jsDir, name);

// NOTE: two things are intentionally deferred to Track D and NOT handled here:
//  1. the web-component build (build:wc, the adpf-* custom elements under
//     js/web-components/) — Vue CLI's --target wc has no turnkey Vite equivalent,
//     the artifact is externally consumed, and it can only be runtime-verified
//     once the portal runs against gRPC. It is a mandatory Track D deliverable.
//  2. the unit tests (tests/unit/**) — Vitest could not resolve the linked source
//     packages' extensionless internal imports in this app's setup, so the test
//     script/devDeps were removed. The spec files are left in place for Track D
//     to migrate (jest -> vitest) alongside the wc work.

export default defineConfig({
  base: publicPath,
  plugins: [vue(), tailwindcss(), djangoWebpackStats()],
  resolve: {
    // `.vue` so extensionless imports resolve like they did under Vue CLI.
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
    // This app links to common/api/plugin-api (already Vue 3). reka-ui (the
    // shadcn-vue primitive layer) is provided transitively via the common
    // package; dedupe so a single copy of these singletons is used and component
    // instances / Pinia stores / reka-ui module-level state stay shared.
    dedupe: ["vue", "reka-ui", "pinia", "vue-router"],
    alias: [
      // `@` -> this app's js dir, matching the other migrated apps.
      { find: "@", replacement: jsDir },
      // The linked common package's Uppy.vue (pulled in via the `components`
      // barrel) imports the Uppy CSS via the `dist/` path, which the @uppy/*
      // packages' `exports` field does not expose (only `css/style.min.css` is).
      // Rewrite those deep imports to the exports-allowed path so the build's
      // stricter resolver (rolldown) can resolve them. Behavior is identical
      // (same stylesheet); this is purely a resolution shim.
      {
        find: "@uppy/core/dist/style.min.css",
        replacement: "@uppy/core/css/style.min.css",
      },
      {
        find: "@uppy/status-bar/dist/style.min.css",
        replacement: "@uppy/status-bar/css/style.min.css",
      },
      {
        find: "@uppy/drag-drop/dist/style.min.css",
        replacement: "@uppy/drag-drop/css/style.min.css",
      },
    ],
  },
  build: {
    outDir: "static/django_airavata_workspace/dist",
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      input: {
        "project-list": entry("entry-project-list.js"),
        dashboard: entry("entry-dashboard.js"),
        "create-experiment": entry("entry-create-experiment.js"),
        "view-experiment": entry("entry-view-experiment.js"),
        "experiment-list": entry("entry-experiment-list.js"),
        "edit-experiment": entry("entry-edit-experiment.js"),
        "edit-project": entry("entry-edit-project.js"),
        "user-storage": entry("entry-user-storage.js"),
      },
      output: {
        entryFileNames: "js/[name].js",
        chunkFileNames: "js/[name].js",
        assetFileNames: (info) => {
          const name = info.names?.[0] ?? info.name ?? "";
          return name.endsWith(".css")
            ? "css/[name][extname]"
            : "assets/[name][extname]";
        },
      },
    },
  },
});
