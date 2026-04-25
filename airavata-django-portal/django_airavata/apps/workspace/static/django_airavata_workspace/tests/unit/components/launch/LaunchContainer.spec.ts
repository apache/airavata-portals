import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LaunchContainer from "../../../../js/containers/LaunchContainer.vue";

vi.mock("django-airavata-common-ui/js/services/launcherService", () => ({
  launcherService: {
    listProjects: vi.fn(),
    listApplications: vi.fn(),
    listUserStorages: vi.fn(),
  },
}));


describe("LaunchContainer", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("starts on tab 1", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();
    expect(w.find("[data-test='active-tab']").attributes("data-active")).toBe("1");
  });

  it("renders the meta header", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();
    expect(w.find("input[data-test='exp-name']").exists()).toBe(true);
  });

  it("only one tab panel is shown at a time", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();
    const visiblePanels = w.findAll("[role='tabpanel']").filter((p) => !p.attributes("hidden"));
    expect(visiblePanels).toHaveLength(1);
  });
});
