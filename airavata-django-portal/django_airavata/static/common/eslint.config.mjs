import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import globals from "globals";

// Flat config (ESLint 9+/10). Replaces the legacy `eslintConfig` block
// (eslint:recommended + plugin:vue/essential). Vue 3 SFCs; the Vue plugin's
// flat config wires up vue-eslint-parser for .vue files.
export default [
  js.configs.recommended,
  ...pluginVue.configs["flat/essential"],
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },
  {
    // The generated shadcn-vue component library (js/components/ui) keeps the
    // upstream single-word file/component names (Button, Input, Card, ...).
    // That is the shadcn-vue convention, so the multi-word-name rule does not
    // apply to it.
    files: ["js/components/ui/**/*.vue"],
    rules: {
      "vue/multi-word-component-names": "off",
    },
  },
];
