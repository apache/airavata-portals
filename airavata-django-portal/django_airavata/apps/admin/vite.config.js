import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(import.meta.dirname, "./static/django_airavata_admin/src");

export default defineAppConfig({
  appLabel: "django_airavata_admin",
  srcDir,
  entries: resolve(srcDir, "main.js"),
});
