import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

const publicPath = "/static/django_airavata_groups/dist/";

const entry = (name) =>
  resolve(__dirname, `static/django_airavata_groups/js/${name}`);

export default defineConfig({
  base: publicPath,
  plugins: [vue(), tailwindcss()],
  // The source uses extensionless `.vue` imports (Vue CLI resolved them
  // automatically); add `.vue` so Vite/Rollup resolves them too. Dedupe Vue and
  // friends so the yarn-linked common/api packages share this package's single
  // copy (avoids "multiple Vue copies"/invalid-hook errors).
  resolve: {
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
    dedupe: ["vue", "reka-ui"],
    alias: {
      // The shadcn-vue UI components live in the linked common package's source
      // and import each other via `@/lib/utils` / `@/components/ui/*`. This app
      // pulls that source into its bundle (via common's globally-registered UI
      // barrel), so `@` must resolve to common's `js` dir for those imports to
      // load. This app has no `@`-prefixed imports of its own.
      "@": resolve(__dirname, "../../static/common/js"),
      // The linked common-ui's Uppy.vue imports Uppy 5.x CSS via the legacy
      // `dist/` path, which Uppy's `exports` field no longer maps when the file
      // is bundled as a linked dependency. Point those deep paths at the real
      // files so resolution succeeds.
      "@uppy/core/dist/style.min.css": "@uppy/core/css/style.min.css",
      "@uppy/status-bar/dist/style.min.css":
        "@uppy/status-bar/css/style.min.css",
      "@uppy/drag-drop/dist/style.min.css":
        "@uppy/drag-drop/css/style.min.css",
    },
  },
  build: {
    outDir: "static/django_airavata_groups/dist",
    manifest: true,
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
