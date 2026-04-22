import { defineVitestConfig } from "@airavata/tooling/vitest.config.js";
import { resolve } from "path";

export default defineVitestConfig({
  srcDir: resolve(import.meta.dirname, "./static/django_airavata_workspace/js"),
});
