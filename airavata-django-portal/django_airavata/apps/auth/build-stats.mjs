// The auth app has no page bundles — login/account self-service is hosted by Keycloak.
// But the 'AUTH' django-webpack-loader config still expects a stats file to exist, and
// `vite build` errors on an empty `input: {}` ("You must supply options.input to rollup").
// So emit an empty-but-valid webpack-stats.json directly instead of running Vite.
import { mkdirSync, writeFileSync } from "node:fs";

const publicPath = "/static/django_airavata_auth/dist/";
const outDir = "static/django_airavata_auth/dist";

mkdirSync(outDir, { recursive: true });
writeFileSync(
  `${outDir}/webpack-stats.json`,
  JSON.stringify({ status: "done", publicPath, chunks: {} }, null, 2) + "\n",
);
console.log("auth: emitted empty webpack-stats.json (no page bundles — Keycloak-hosted)");
