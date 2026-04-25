import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import FileInputRow from "../../../../js/components/launch/FileInputRow.vue";

const STORAGES = [
  { storage_id: "my-home", name: "My Home", is_primary: true },
  { storage_id: "scratch", name: "Scratch", is_primary: false },
];

describe("FileInputRow", () => {
  it("emits update:modelValue when storage changes", async () => {
    const w = mount(FileInputRow, {
      props: {
        descriptor: { name: "sim_dir", type: "dir", required: true },
        modelValue: { storage_id: "my-home", path: "" },
        storages: STORAGES,
      },
    });
    await w.find("select").setValue("scratch");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([{ storage_id: "scratch", path: "" }]);
  });

  it("emits update:modelValue when path changes", async () => {
    const w = mount(FileInputRow, {
      props: {
        descriptor: { name: "sim_dir", type: "dir", required: true },
        modelValue: { storage_id: "my-home", path: "" },
        storages: STORAGES,
      },
    });
    await w.find("input[data-test='file-path-sim_dir']").setValue("/home/x/sim");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([{ storage_id: "my-home", path: "/home/x/sim" }]);
  });

  it("renders a stage-in badge", () => {
    const w = mount(FileInputRow, {
      props: {
        descriptor: { name: "sim_dir", type: "dir", required: true },
        modelValue: null,
        storages: STORAGES,
      },
    });
    expect(w.find("[data-test='io-badge']").text()).toMatch(/stage-in/i);
  });
});
