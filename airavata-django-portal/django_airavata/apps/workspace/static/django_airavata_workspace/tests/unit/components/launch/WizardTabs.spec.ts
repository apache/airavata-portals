import { mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import WizardTabs from "../../../../js/components/launch/WizardTabs.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

describe("WizardTabs", () => {
  beforeEach(() => setActivePinia(createPinia()));

  function makeMount(active: 1 | 2 | 3 = 1) {
    return mount(WizardTabs, { props: { active }, global: { stubs: { transition: false } } });
  }

  it("renders three tab buttons", () => {
    const w = makeMount();
    expect(w.findAll("button[role='tab']")).toHaveLength(3);
  });

  it("disables tabs 2 and 3 when tab 1 is invalid", () => {
    const w = makeMount();
    const tabs = w.findAll("button[role='tab']");
    expect(tabs[1].attributes("disabled")).toBeDefined();
    expect(tabs[2].attributes("disabled")).toBeDefined();
  });

  it("emits update:active when allowed tab clicked", async () => {
    const store = useLaunchStore();
    // Force tab 1 valid by spying on the getter
    Object.defineProperty(store, "tab1Valid", { value: true });
    const w = makeMount();
    await w.findAll("button[role='tab']")[1].trigger("click");
    expect(w.emitted("update:active")?.[0]).toEqual([2]);
  });

  it("does not emit update:active for a disabled tab", async () => {
    const w = makeMount();
    await w.findAll("button[role='tab']")[1].trigger("click");
    expect(w.emitted("update:active")).toBeUndefined();
  });
});
