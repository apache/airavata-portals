import js from "@eslint/js";
import vuePlugin from "eslint-plugin-vue";
import vueParser from "vue-eslint-parser";
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

      // Vue Style Guide + Vue 2 deprecation rules demoted to warn.
      // Track A's <script setup lang="ts"> rewrite will obsolete most of
      // these (defineEmits/defineProps with TS types, modern slot syntax,
      // no Options API ordering to police). Track C lands a clean build
      // + visible warnings; Track A re-enables full strict when the
      // Options API is gone.
      "vue/require-explicit-emits": "warn",
      "vue/require-default-prop": "warn",
      "vue/require-prop-types": "warn",
      "vue/order-in-components": "warn",
      "vue/attributes-order": "warn",
      "vue/first-attribute-linebreak": "warn",
      "vue/component-definition-name-casing": "warn",
      "vue/prop-name-casing": "warn",
      "vue/no-deprecated-slot-attribute": "warn",
      "vue/no-deprecated-slot-scope-attribute": "warn",
      "vue/no-deprecated-delete-set": "warn",
      "vue/no-deprecated-events-api": "warn",
      "vue/no-deprecated-v-on-native-modifier": "warn",
      "vue/multi-word-component-names": "off",
      "vue/no-v-html": "warn",
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
