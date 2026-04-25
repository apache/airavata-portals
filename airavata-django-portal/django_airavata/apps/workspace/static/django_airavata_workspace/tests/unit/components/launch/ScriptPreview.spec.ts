import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ScriptPreview from "../../../../js/components/launch/ScriptPreview.vue";
import InvocationCommand from "../../../../js/components/launch/InvocationCommand.vue";

describe("ScriptPreview", () => {
  it("renders the script in a code block", () => {
    const w = mount(ScriptPreview, { props: { script: "#!/bin/bash\necho hi\n" } });
    expect(w.find("pre code").text()).toContain("echo hi");
  });

  it("is read-only (no contenteditable)", () => {
    const w = mount(ScriptPreview, { props: { script: "x" } });
    expect(w.find("pre").attributes("contenteditable")).toBeUndefined();
  });
});

describe("InvocationCommand", () => {
  it("renders the command", () => {
    const w = mount(InvocationCommand, { props: { command: "sbatch /tmp/run.sh" } });
    expect(w.text()).toContain("sbatch /tmp/run.sh");
  });
});
