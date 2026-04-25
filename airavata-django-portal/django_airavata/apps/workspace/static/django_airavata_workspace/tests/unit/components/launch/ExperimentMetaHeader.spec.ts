import { mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import ExperimentMetaHeader from "../../../../js/components/launch/ExperimentMetaHeader.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

const PROJECTS = [
  { project_id: "p1", name: "my-lab-2026" },
  { project_id: "p2", name: "shared" },
];

describe("ExperimentMetaHeader", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("binds name input to the store", async () => {
    const w = mount(ExperimentMetaHeader, { props: { projects: PROJECTS } });
    await w.find("input[data-test='exp-name']").setValue("my-run");
    expect(useLaunchStore().draft.name).toBe("my-run");
  });

  it("binds project dropdown to the store", async () => {
    const w = mount(ExperimentMetaHeader, { props: { projects: PROJECTS } });
    await w.find("select[data-test='exp-project']").setValue("p2");
    expect(useLaunchStore().draft.project_id).toBe("p2");
  });

  it("renders description as a textarea", () => {
    const w = mount(ExperimentMetaHeader, { props: { projects: PROJECTS } });
    expect(w.find("textarea[data-test='exp-description']").exists()).toBe(true);
  });
});
