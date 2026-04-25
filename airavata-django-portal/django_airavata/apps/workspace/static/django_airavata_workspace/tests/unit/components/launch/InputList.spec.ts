import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import InputList from "../../../../js/components/launch/InputList.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

const APP = {
  app_id: "namd", name: "NAMD", category: "MD",
  content: { kind: "github" as const, url: "g" },
  interfaces: [{
    name: "run",
    inputs: [
      { name: "sim_dir", type: "dir" as const, required: true },
      { name: "steps", type: "int" as const, required: true },
    ],
    outputs: [],
  }],
};

const STORAGES = [{ storage_id: "my-home", name: "My Home", is_primary: true }];

describe("InputList", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    const s = useLaunchStore();
    s.pickApp(APP);
    s.pickInterface("run");
  });

  it("renders one row per declared input", () => {
    const w = mount(InputList, { props: { storages: STORAGES } });
    expect(w.findAll("[data-test='input-row']")).toHaveLength(2);
  });

  it("scalar input writes through to the store", async () => {
    const w = mount(InputList, { props: { storages: STORAGES } });
    await w.find("input[data-test='scalar-steps']").setValue("5000");
    expect(useLaunchStore().draft.inputs.steps).toBe(5000);
  });

  it("file input writes through to the store", async () => {
    const w = mount(InputList, { props: { storages: STORAGES } });
    await w.find("input[data-test='file-path-sim_dir']").setValue("/data");
    expect(useLaunchStore().draft.inputs.sim_dir).toEqual({ storage_id: "", path: "/data" });
  });
});
