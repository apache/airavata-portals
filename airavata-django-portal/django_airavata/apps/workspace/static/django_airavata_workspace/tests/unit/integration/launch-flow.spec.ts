import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LaunchContainer from "../../../js/containers/LaunchContainer.vue";

const APP = {
  app_id: "namd", name: "NAMD", category: "MD",
  content: { kind: "github" as const, url: "g" },
  interfaces: [{
    name: "run",
    inputs: [
      { name: "sim_dir", type: "dir" as const, required: true },
      { name: "steps", type: "int" as const, required: true },
    ],
    outputs: [{ name: "trajectory", type: "file" as const }],
  }],
};

const PROFILE = {
  project_id: "p1", allocation_id: "NSF-1",
  compute_resources: [{
    compute_resource_id: "bridges-2", name: "Bridges-2",
    mapped_storage: { storage_id: "scratch", scratch_path: "/scratch/p1" },
    partitions: [{ name: "RM", max_walltime: "48:00:00", max_nodes: 64, cpus_per_node: 128 }],
  }],
};

vi.mock("django-airavata-common-ui/js/services/launcherService", () => ({
  launcherService: {
    listApplications: vi.fn(),
    listUserStorages: vi.fn(),
    listProjects: vi.fn(),
    getProjectResourceProfile: vi.fn(),
    generatePreview: vi.fn(),
    launchExperiment: vi.fn(),
  },
}));

import { launcherService } from "django-airavata-common-ui/js/services/launcherService";

describe("launch flow integration", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    vi.mocked(launcherService.listApplications).mockResolvedValue({ results: [APP] });
    vi.mocked(launcherService.listUserStorages).mockResolvedValue({
      results: [{ storage_id: "my-home", name: "Home", is_primary: true }],
    });
    vi.mocked(launcherService.listProjects).mockResolvedValue({
      results: [{ project_id: "p1", name: "lab" }],
    });
    vi.mocked(launcherService.getProjectResourceProfile).mockResolvedValue(PROFILE);
    vi.mocked(launcherService.generatePreview).mockResolvedValue({
      invocation_command: "sbatch /tmp/run.sh",
      script_contents: "#!/bin/bash\necho hi",
      warnings: [],
    });
    vi.mocked(launcherService.launchExperiment).mockResolvedValue({ experiment_id: "exp-7" });
    Object.defineProperty(window, "location", {
      value: { href: "http://localhost/", assign: vi.fn() }, writable: true,
    });
    vi.spyOn(window.history, "replaceState").mockImplementation(() => {});
  });

  it("walks tab 1 → tab 2 → tab 3 → launch", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();

    // Meta
    await w.find("input[data-test='exp-name']").setValue("test-run");
    await w.find("select[data-test='exp-project']").setValue("p1");

    // App + interface
    await w.find("[data-test='app-tile-namd']").trigger("click");
    await flushPromises();
    await w.find("[data-test='iface-card-run']").trigger("click");

    // Inputs + output
    // sim_dir is a dir input: its storage select is the sibling select immediately
    // before the file-path input (inside the same flex row div).
    const simDirInput = w.find("input[data-test='file-path-sim_dir']");
    // The FileInputRow renders: select (storage) | input (path) — find all selects
    // and pick the one whose next input sibling has data-test='file-path-sim_dir'
    const simDirStorageSelect = w.findAll("select").find((s) => {
      const next = s.element.nextElementSibling;
      return next instanceof HTMLInputElement && next.dataset.test === "file-path-sim_dir";
    });
    if (simDirStorageSelect) await simDirStorageSelect.setValue("my-home");
    await simDirInput.setValue("/x");
    await w.find("input[data-test='scalar-steps']").setValue("100");
    // Output: find the storage select within the trajectory output row
    const outSelect = w.findAll("select").find((s) => s.element.parentElement?.outerHTML.includes("trajectory"));
    if (outSelect) await outSelect.setValue("my-home");
    await w.find("input[data-test='file-out-path-trajectory']").setValue("/y");

    // Tab 2
    await w.findAll("button[role='tab']")[1].trigger("click");
    await flushPromises();
    await w.find("select[data-test='cr']").setValue("bridges-2");
    await w.find("select[data-test='partition']").setValue("RM");

    // Tab 3
    await w.findAll("button[role='tab']")[2].trigger("click");
    await flushPromises();
    expect(w.text()).toContain("sbatch /tmp/run.sh");
    await w.find("button[data-test='launch']").trigger("click");
    await flushPromises();
    expect(window.location.href).toBe("/workspace/experiments/exp-7");
  });
});
