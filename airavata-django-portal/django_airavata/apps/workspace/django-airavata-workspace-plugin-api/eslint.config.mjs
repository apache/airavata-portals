import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import globals from "globals";

// Flat config (ESLint 9+/10). Replaces the legacy `eslintConfig` block
// (eslint:recommended + plugin:vue/essential). This package is plain ES-module
// JS that defines Vue 3 component options (the InputEditorMixin); the Vue
// plugin's flat config keeps the vue/* rules available even though there are no
// .vue SFCs here.
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
];
