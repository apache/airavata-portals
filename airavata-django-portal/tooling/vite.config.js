import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

/**
 * Shared Vite config factory for every workspace.
 *
 * @param {object} opts
 * @param {string} opts.appLabel       e.g. "django_airavata_workspace"
 * @param {string} opts.srcDir         absolute path to the workspace's JS source dir
 * @param {Record<string,string>|string} opts.entries  Rollup input(s)
 * @param {boolean} [opts.isLibrary]   true for api / plugin-api (library mode)
 * @param {object}  [opts.overrides]   shallow-merged over the generated config
 */
export function defineAppConfig({ appLabel, srcDir, entries, isLibrary = false, overrides = {} }) {
  const base = isLibrary ? "/" : `/static/${appLabel}/dist/`;
  return defineConfig({
    plugins: [vue()],
    base,
    build: {
      manifest: isLibrary ? false : "manifest.json",
      outDir: resolve(srcDir, "../dist"),
      rollupOptions: { input: entries },
    },
    css: { preprocessorOptions: { scss: { quietDeps: true } } },
    resolve: {
      extensions: [".vue", ".ts", ".js", ".json"],
      alias: { "@": srcDir },
    },
    server: { port: 9000, origin: "http://localhost:9000" },
    ...overrides,
  });
}
