import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Tab1ApplicationInputs from "../../../../js/components/launch/Tab1ApplicationInputs.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

vi.mock("django-airavata-common-ui/js/services/launcherService", () => ({
  launcherService: {
    listApplications: vi.fn(),
    listUserStorages: vi.fn(),
  },
}));

describe("Tab1ApplicationInputs", () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    const { launcherService } = await import(
      "django-airavata-common-ui/js/services/launcherService"
    );
    vi.mocked(launcherService.listApplications).mockResolvedValue({
      results: [{
        app_id: "namd", name: "NAMD", category: "MD",
        content: { kind: "github", url: "g" }, interfaces: [],
      }],
    });
    vi.mocked(launcherService.listUserStorages).mockResolvedValue({
      results: [{ storage_id: "my-home", name: "My Home", is_primary: true }],
    });
  });

  it("loads applications + storages on mount", async () => {
    const w = mount(Tab1ApplicationInputs);
    await flushPromises();
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(1);
    expect(useLaunchStore().storages).toHaveLength(1);
  });

  it("does not render the inputs section before an app+interface are picked", async () => {
    const w = mount(Tab1ApplicationInputs);
    await flushPromises();
    expect(w.find("[data-test='inputs-section']").exists()).toBe(false);
  });
});
