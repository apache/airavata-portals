import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

const publicPath = "/static/django_airavata_dataparsers/dist/";

const entry = (name) =>
  resolve(__dirname, `static/django_airavata_dataparsers/js/${name}`);

export default defineConfig({
  base: publicPath,
  plugins: [vue(), tailwindcss()],
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
    manifest: true,
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
