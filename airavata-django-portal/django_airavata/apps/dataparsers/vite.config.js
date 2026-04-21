import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(import.meta.dirname, "./static/django_airavata_dataparsers/js");

export default defineAppConfig({
  appLabel: "django_airavata_dataparsers",
  srcDir,
  entries: {
    "parser-details": resolve(srcDir, "entry-parser-details.js"),
    "parser-list": resolve(srcDir, "parser-listing-entry-point.js"),
    "parser-edit": resolve(srcDir, "parser-edit-entry-point.js"),
  },
});
