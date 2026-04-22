import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

/**
 * Shared Vitest config factory.
 *
 * @param {object} opts
 * @param {string} opts.srcDir  absolute path to workspace's JS/TS source dir
 * @param {object} [opts.overrides]  shallow-merged over the generated config
 */
export function defineVitestConfig({ srcDir, overrides = {} }) {
  return defineConfig({
    plugins: [vue()],
    resolve: {
      alias: { "@": srcDir },
      extensions: [".vue", ".ts", ".js", ".json"],
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: [resolve(import.meta.dirname, "./vitest-setup.ts")],
      include: ["**/*.{test,spec}.{js,ts,mjs}", "**/tests/**/*.{test,spec}.{js,ts}"],
      exclude: ["**/node_modules/**", "**/dist/**", "**/tests/e2e/**"],
      clearMocks: true,
      restoreMocks: true,
      passWithNoTests: true,
    },
    ...overrides,
  });
}
