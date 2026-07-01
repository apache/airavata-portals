import { resolve } from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

const publicPath = "/static/django_airavata_admin/dist/";
const srcDir = resolve(__dirname, "static/django_airavata_admin/src");
const commonJsDir = resolve(__dirname, "../../static/common/js");
// The common-ui workspace's Uppy.vue (pulled in via the common-ui barrel) imports
// `@uppy/<pkg>/dist/style.min.css`, but Uppy 5's `exports` field only maps
// `./css/style.min.css`. Under the strict rolldown resolver these deep paths fail,
// so rewrite them to the exports-allowed path (resolved from the hoisted root
// node_modules under npm workspaces). Behavior is identical (same stylesheet);
// this is purely a resolution shim. (Admin doesn't use Uppy itself.)
const uppyCssAliases = ["core", "status-bar", "drag-drop"].map((pkg) => ({
  find: `@uppy/${pkg}/dist/style.min.css`,
  replacement: `@uppy/${pkg}/css/style.min.css`,
}));

export default defineConfig({
  base: publicPath,
  plugins: [vue(), tailwindcss()],
  resolve: {
    // `@` -> src (Vue CLI default, used by the unit specs); `.vue` so extensionless
    // imports resolve like they did under Vue CLI. The linked common package's
    // shadcn-vue UI components (pulled in via common's globally-registered barrel)
    // import each other via `@/lib/utils` and `@/components/ui/*`; those `@` paths
    // must resolve against common's `js` dir, so map them explicitly before the
    // app-local `@` -> src fallback (more specific aliases first).
    alias: [
      { find: "@/lib", replacement: resolve(commonJsDir, "lib") },
      {
        find: "@/components/ui",
        replacement: resolve(commonJsDir, "components/ui"),
      },
      { find: "@", replacement: srcDir },
      ...uppyCssAliases,
    ],
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json", ".vue"],
    // This package links to common/api (already Vue 3). Dedupe so a single copy
    // of these singletons is used and Vue's runtime hooks stay valid.
    dedupe: ["vue", "reka-ui", "pinia", "vue-router"],
  },
  build: {
    outDir: "static/django_airavata_admin/dist",
    manifest: true,
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
