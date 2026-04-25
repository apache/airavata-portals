import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ScalarInputRow from "../../../../js/components/launch/ScalarInputRow.vue";

describe("ScalarInputRow", () => {
  it("renders a number input for type=int", async () => {
    const w = mount(ScalarInputRow, {
      props: { descriptor: { name: "steps", type: "int", required: true }, modelValue: null },
    });
    const input = w.find("input[data-test='scalar-steps']");
    expect(input.attributes("type")).toBe("number");
  });

  it("emits update:modelValue on input", async () => {
    const w = mount(ScalarInputRow, {
      props: { descriptor: { name: "steps", type: "int", required: true }, modelValue: null },
    });
    await w.find("input").setValue("42");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([42]);
  });

  it("renders a select for enum descriptors", () => {
    const w = mount(ScalarInputRow, {
      props: {
        descriptor: { name: "mode", type: "enum", required: true, options: ["a", "b"] },
        modelValue: null,
      },
    });
    expect(w.find("select").exists()).toBe(true);
  });
});
