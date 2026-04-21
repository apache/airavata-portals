# @airavata/tooling

Shared JavaScript tooling configs for the Airavata Django Portal monorepo.

## What it exposes

- `eslint.config.js` — ESLint 9 flat config. Strict: `@eslint/js recommended` +
  `eslint-plugin-vue/flat/recommended` + `eslint-config-prettier`.
- `prettier.config.js` — Prettier rules (printWidth 100, trailing comma, etc.).
- `vite.config.js` — exports `defineAppConfig({ appLabel, srcDir, entries, isLibrary, overrides })`
  helper. Every workspace's `vite.config.js` is a 6-10 line call to this.
- `tsconfig.base.json` — `strict: true`, `allowJs: false`. Extended by each
  Vue workspace's `jsconfig.json`.

## Consuming from a workspace

```js
// eslint.config.js
export { default } from "@airavata/tooling/eslint.config.js";
```

```js
// prettier.config.js
module.exports = require("@airavata/tooling/prettier.config.js");
```

```js
// vite.config.js
import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

export default defineAppConfig({
  appLabel: "django_airavata_<label>",
  srcDir: resolve(import.meta.dirname, "./static/django_airavata_<label>/src"),
  entries: resolve(import.meta.dirname, "./static/django_airavata_<label>/src/main.js"),
});
```

```json
// jsconfig.json
{ "extends": "@airavata/tooling/tsconfig.base.json" }
```

## Adding a new workspace

1. Register the workspace path in the root `package.json`'s `workspaces` array.
2. Add the 4 config stanzas above.
3. Ensure the workspace's `package.json` lists `@airavata/tooling` as a
   `devDependency` (npm workspaces hoist it automatically, but the entry
   makes the dep graph explicit).
4. Run `npm install` at the repo root so the symlink is created.
