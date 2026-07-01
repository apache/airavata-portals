import { resolve } from "node:path";
import { defineConfig } from "vite";

// Public URL prefix Django serves this app's built assets from. Must match the
// AppConfig.merge_settings "base" and the app's static dir name.
const publicPath = "/static/{{ cookiecutter.project_slug }}/dist/";

export default defineConfig({
  base: publicPath,
  build: {
    outDir: "dist",
    // Emit dist/.vite/manifest.json for the portal's vite_js / vite_css tags.
    manifest: true,
    emptyOutDir: true,
    rollupOptions: {
      // The input key ("main") is the bundle name the template tags look up.
      input: {
        main: resolve(__dirname, "js/main.js"),
      },
    },
  },
});
