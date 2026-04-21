import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(import.meta.dirname, "./static/django_airavata_auth/js");

export default defineAppConfig({
  appLabel: "django_airavata_auth",
  srcDir,
  entries: {
    "user-profile": resolve(srcDir, "entry-user-profile.js"),
  },
});
