import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import type { InterfaceDescriptor } from "django-airavata-common-ui/js/stores/launch-types";

const RUN_IFACE: InterfaceDescriptor = {
  name: "run",
  inputs: [
    { name: "sim_dir", type: "dir", required: true },
    { name: "steps", type: "int", required: true },
  ],
  outputs: [{ name: "trajectory", type: "file" }],
};

describe("useLaunchStore", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("starts with an invalid empty draft", () => {
    const s = useLaunchStore();
    expect(s.tab1Valid).toBe(false);
    expect(s.tab2Valid).toBe(false);
  });

  it("validates tab 1 once name+project+app+iface+inputs+outputs are set", () => {
    const s = useLaunchStore();
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    s.pickApp({ app_id: "namd", name: "NAMD", category: "MD",
                content: { kind: "github", url: "g" }, interfaces: [RUN_IFACE] });
    s.pickInterface("run");
    s.setInput("sim_dir", { storage_id: "my-home", path: "/x" });
    s.setInput("steps", 100);
    s.setOutput("trajectory", { storage_id: "my-home", path: "/y" });
    expect(s.tab1Valid).toBe(true);
  });

  it("clears interface + inputs when app changes", () => {
    const s = useLaunchStore();
    s.pickApp({ app_id: "namd", name: "NAMD", category: "MD",
                content: { kind: "github", url: "g" }, interfaces: [RUN_IFACE] });
    s.pickInterface("run");
    s.setInput("steps", 100);
    s.pickApp({ app_id: "gromacs", name: "GROMACS", category: "MD",
                content: { kind: "tarball", url: "t" }, interfaces: [] });
    expect(s.draft.interface_name).toBeNull();
    expect(s.draft.inputs).toEqual({});
  });

  it("clears compute fields when project changes", () => {
    const s = useLaunchStore();
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    s.setRuntime({ compute_resource_id: "cr-1", partition: "RM", walltime: "01:00:00", nodes: 1, cpus_per_node: 8 });
    s.setMeta({ name: "x", project_id: "p2", description: "" });
    expect(s.draft.runtime.compute_resource_id).toBeNull();
    expect(s.draft.runtime.partition).toBeNull();
  });

  it("computes a stable hash that changes only on draft change", () => {
    const s = useLaunchStore();
    const h1 = s.draftHash;
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    expect(s.draftHash).not.toBe(h1);
    const h2 = s.draftHash;
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    expect(s.draftHash).toBe(h2);
  });
});
