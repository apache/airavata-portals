import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(import.meta.dirname, "./static/django_airavata_workspace/js");

export default defineAppConfig({
  appLabel: "django_airavata_workspace",
  srcDir,
  entries: {
    dashboard: resolve(srcDir, "entry-dashboard.js"),
    "project-list": resolve(srcDir, "entry-project-list.js"),
    applications: resolve(srcDir, "entry-applications.js"),
    "create-experiment": resolve(srcDir, "entry-create-experiment.js"),
    "view-experiment": resolve(srcDir, "entry-view-experiment.js"),
    "experiment-list": resolve(srcDir, "entry-experiment-list.js"),
    "edit-experiment": resolve(srcDir, "entry-edit-experiment.js"),
    "edit-project": resolve(srcDir, "entry-edit-project.js"),
    "user-storage": resolve(srcDir, "entry-user-storage.js"),
    compute: resolve(srcDir, "entry-compute.js"),
    datasets: resolve(srcDir, "entry-datasets.js"),
    "datasets-list": resolve(srcDir, "entry-datasets-list.js"),
    credentials: resolve(srcDir, "entry-credentials.js"),
    "gateway-settings": resolve(srcDir, "entry-gateway-settings.js"),
    "storage-detail": resolve(srcDir, "entry-storage-detail.js"),
    "compute-detail": resolve(srcDir, "entry-compute-detail.js"),
    "project-overview": resolve(srcDir, "entry-project-overview.js"),
    "application-editor": resolve(srcDir, "entry-application-editor.js"),
    launch: resolve(srcDir, "entry-launch.ts"),
  },
});
