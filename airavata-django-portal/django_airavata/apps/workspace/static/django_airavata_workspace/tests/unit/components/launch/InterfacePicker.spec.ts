import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import InterfacePicker from "../../../../js/components/launch/InterfacePicker.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

const APP = {
  app_id: "namd", name: "NAMD", category: "MD",
  content: { kind: "github" as const, url: "g" },
  interfaces: [
    { name: "compile", inputs: [], outputs: [] },
    { name: "run", inputs: [{ name: "x", type: "int" as const, required: true }], outputs: [] },
  ],
};

describe("InterfacePicker", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useLaunchStore().pickApp(APP);
  });

  it("renders one card per interface", () => {
    const w = mount(InterfacePicker);
    expect(w.findAll("[data-test='iface-card']")).toHaveLength(2);
  });

  it("clicking a card sets interface_name in the store", async () => {
    const w = mount(InterfacePicker);
    await w.find("[data-test='iface-card-run']").trigger("click");
    expect(useLaunchStore().draft.interface_name).toBe("run");
  });

  it("renders an input/output signature line per card", () => {
    const w = mount(InterfacePicker);
    const sig = w.find("[data-test='iface-sig-run']").text();
    expect(sig).toContain("x: int");
  });
});
