import js from "@eslint/js";
import globals from "globals";

// Flat config (ESLint 9+/10). Replaces the legacy `eslintConfig` block that used
// `eslint:recommended` + env browser/node. This package is plain ES-module JS
// (models and service wrappers for the REST API).
export default [
  js.configs.recommended,
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
