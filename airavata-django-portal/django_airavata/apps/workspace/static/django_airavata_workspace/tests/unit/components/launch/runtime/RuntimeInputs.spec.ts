import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import RuntimeInputs from "../../../../../js/components/launch/runtime/RuntimeInputs.vue";

const PROFILE = {
  project_id: "p1", allocation_id: "NSF-1",
  compute_resources: [{
    compute_resource_id: "bridges-2", name: "Bridges-2",
    mapped_storage: { storage_id: "scratch", scratch_path: "/scratch/p1" },
    partitions: [{ name: "RM", max_walltime: "48:00:00", max_nodes: 64, cpus_per_node: 128 }],
  }],
};

describe("RuntimeInputs", () => {
  it("populates compute resource dropdown from profile", () => {
    const w = mount(RuntimeInputs, {
      props: { profile: PROFILE, modelValue: { compute_resource_id: null, partition: null,
              walltime: "01:00:00", nodes: 1, cpus_per_node: 1 } },
    });
    expect(w.find("select[data-test='cr']").findAll("option").map((o) => o.text())).toContain("Bridges-2");
  });

  it("emits update:modelValue when the resource changes", async () => {
    const w = mount(RuntimeInputs, {
      props: { profile: PROFILE, modelValue: { compute_resource_id: null, partition: null,
              walltime: "01:00:00", nodes: 1, cpus_per_node: 1 } },
    });
    await w.find("select[data-test='cr']").setValue("bridges-2");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([
      expect.objectContaining({ compute_resource_id: "bridges-2", partition: null }),
    ]);
  });

  it("limits partition options to the chosen resource", async () => {
    const w = mount(RuntimeInputs, {
      props: { profile: PROFILE, modelValue: { compute_resource_id: "bridges-2", partition: null,
              walltime: "01:00:00", nodes: 1, cpus_per_node: 1 } },
    });
    const opts = w.find("select[data-test='partition']").findAll("option").map((o) => o.text());
    expect(opts).toContain("RM");
    expect(opts).not.toContain("nonexistent");
  });
});
