import js from "@eslint/js";
import vuePlugin from "eslint-plugin-vue";
import vueParser from "vue-eslint-parser";
import tsParser from "@typescript-eslint/parser";
import prettierConfig from "eslint-config-prettier";
import globals from "globals";

export default [
  // Global ignores MUST live in a config object with ONLY the `ignores` key —
  // in ESLint 9 flat config, `ignores` next to `rules` only scopes ignores
  // to that one config object. Missing this turned ignores into no-ops
  // across plugin configs and made eslint lint built /dist/ artefacts.
  {
    ignores: [
      "**/dist/**",
      "**/node_modules/**",
      "**/*.d.ts",
      "**/static/**/manifest.json",
      "**/*.min.js",
      "**/vendor/**",
    ],
  },
  js.configs.recommended,
  ...vuePlugin.configs["flat/recommended"],
  prettierConfig,
  {
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        // Use TypeScript parser for <script lang="ts"> blocks inside .vue files
        parser: tsParser,
        ecmaVersion: 2024,
        sourceType: "module",
      },
      ecmaVersion: 2024,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.es2024,
        ...globals.node,
      },
    },
    rules: {
      // Bug-catching rules stay strict.
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-undef": "error",
      "no-unreachable": "error",
      eqeqeq: ["error", "always"],

      // Vue 3 parsing / runtime errors stay strict.
      "vue/no-parsing-error": "error",
      "vue/no-mutating-props": "error",
      "vue/no-unused-components": "error",

      // Vue Style Guide + Vue 2 deprecation rules — all re-elevated to error
      // now that Track A's <script setup lang="ts"> rewrite is complete and
      // all 179 .vue files are clean (M7 final).
      "vue/require-explicit-emits": "error",
      "vue/require-default-prop": "error",
      "vue/require-prop-types": "error",
      "vue/order-in-components": "error",
      "vue/attributes-order": "error",
      "vue/first-attribute-linebreak": "error",
      "vue/component-definition-name-casing": "error",
      "vue/prop-name-casing": "error",
      "vue/no-deprecated-slot-attribute": "error",
      "vue/no-deprecated-slot-scope-attribute": "error",
      "vue/no-deprecated-delete-set": "error",
      "vue/no-deprecated-events-api": "error",
      "vue/no-deprecated-v-on-native-modifier": "error",
      "vue/multi-word-component-names": "off",
      "vue/no-v-html": "warn",  // Intentional: Wagtail CMS content — acceptable XSS risk
    },
  },
  // Test files: Vitest/Jest globals.
  {
    files: ["**/*.{test,spec}.{js,ts,mjs}", "**/tests/**/*.{js,ts,mjs}"],
    languageOptions: {
      globals: {
        describe: "readonly",
        it: "readonly",
        test: "readonly",
        expect: "readonly",
        beforeAll: "readonly",
        beforeEach: "readonly",
        afterAll: "readonly",
        afterEach: "readonly",
        vi: "readonly",
        jest: "readonly",
      },
    },
  },
];
