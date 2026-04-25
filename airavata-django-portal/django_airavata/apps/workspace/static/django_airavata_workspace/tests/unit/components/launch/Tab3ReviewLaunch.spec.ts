import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Tab3ReviewLaunch from "../../../../js/components/launch/Tab3ReviewLaunch.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

vi.mock("django-airavata-common-ui/js/services/launcherService", () => ({
  launcherService: {
    generatePreview: vi.fn(),
    launchExperiment: vi.fn(),
  },
}));

import { launcherService } from "django-airavata-common-ui/js/services/launcherService";

const NAV = vi.fn();
Object.defineProperty(window, "location", { value: { href: "/", assign: NAV }, writable: true });

describe("Tab3ReviewLaunch", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.mocked(launcherService.generatePreview).mockResolvedValue({
      invocation_command: "sbatch /tmp/run.sh",
      script_contents: "#!/bin/bash\necho hi\n",
      warnings: ["check walltime"],
    });
    vi.mocked(launcherService.launchExperiment).mockResolvedValue({ experiment_id: "exp-42" });
    NAV.mockClear();
    window.location.href = "/";
  });

  it("renders the preview after fetch", async () => {
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    expect(w.text()).toContain("sbatch /tmp/run.sh");
    expect(w.text()).toContain("echo hi");
  });

  it("renders warnings as a list", async () => {
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    expect(w.find("[data-test='warnings']").text()).toContain("check walltime");
  });

  it("disables launch when preview failed", async () => {
    vi.mocked(launcherService.generatePreview).mockRejectedValueOnce(new Error("nope"));
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    expect(w.find("button[data-test='launch']").attributes("disabled")).toBeDefined();
  });

  it("redirects on successful launch", async () => {
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    await w.find("button[data-test='launch']").trigger("click");
    await flushPromises();
    expect(window.location.href).toBe("/workspace/experiments/exp-42");
  });
});
