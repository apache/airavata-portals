import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Tab2Runtime from "../../../../js/components/launch/Tab2Runtime.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

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
    getProjectResourceProfile: vi.fn(),
  },
}));

import { launcherService } from "django-airavata-common-ui/js/services/launcherService";

describe("Tab2Runtime", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.mocked(launcherService.getProjectResourceProfile).mockResolvedValue(PROFILE);
    useLaunchStore().setMeta({ name: "x", project_id: "p1", description: "" });
  });

  it("renders the readout once a CR is picked", async () => {
    const w = mount(Tab2Runtime);
    await flushPromises();
    useLaunchStore().setRuntime({
      compute_resource_id: "bridges-2", partition: "RM",
      walltime: "01:00:00", nodes: 1, cpus_per_node: 8,
    });
    await flushPromises();
    expect(w.text()).toContain("NSF-1");
    expect(w.text()).toContain("bridges-2");
    expect(w.text()).toContain("/scratch/p1");
  });

  it("re-fetches the profile when project changes", async () => {
    const w = mount(Tab2Runtime);
    await flushPromises();
    useLaunchStore().setMeta({ name: "x", project_id: "p2", description: "" });
    await flushPromises();
    expect(launcherService.getProjectResourceProfile).toHaveBeenCalledWith("p2");
    expect(w).toBeTruthy();
  });
});
