import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(import.meta.dirname, "./js");

export default defineAppConfig({
  appLabel: "common",
  srcDir,
  entries: {
    app: resolve(srcDir, "main.js"),
    cms: resolve(srcDir, "cms.js"),
    notices: resolve(srcDir, "notices.js"),
  },
});
