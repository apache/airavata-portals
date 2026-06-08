import { resolve } from "node:path";
import { defineConfig } from "vite";

// UMD/CJS library for external workspace plugin apps (custom input editors).
// django-airavata-api is a peer dependency, externalized and provided as the
// global AiravataAPI in the UMD build (matching the old webpack externals).
// Internal/source consumers use the "module" entry (./js/index.js) directly.
// The CJS output keeps the package "main" (./dist/index.common.js) contract.
export default defineConfig({
  // This package is nested under apps/workspace/; pin an empty PostCSS config so
  // Vite doesn't walk up and pick up the parent app's autoprefixer config (the
  // library has no CSS of its own).
  css: { postcss: {} },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "js/index.js"),
      name: "index",
      formats: ["umd", "cjs"],
      fileName: (format) =>
        format === "cjs" ? "index.common.js" : "index.umd.js",
    },
    rollupOptions: {
      external: ["django-airavata-api"],
      output: {
        // index.js exposes both a default object and named exports; keep named
        // exports primary (the documented `import { InputEditorMixin }` usage).
        exports: "named",
        globals: { "django-airavata-api": "AiravataAPI" },
      },
    },
  },
});
