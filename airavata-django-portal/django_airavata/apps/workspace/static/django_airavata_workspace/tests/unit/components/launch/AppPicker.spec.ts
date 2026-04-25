import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import AppPicker from "../../../../js/components/launch/AppPicker.vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

const APPS = [
  { app_id: "namd", name: "NAMD", category: "Molecular Dynamics",
    content: { kind: "github" as const, url: "g" }, interfaces: [] },
  { app_id: "gromacs", name: "GROMACS", category: "Molecular Dynamics",
    content: { kind: "tarball" as const, url: "t" }, interfaces: [] },
  { app_id: "alphafold", name: "AlphaFold", category: "ML / AI",
    content: { kind: "github" as const, url: "g" }, interfaces: [] },
];

describe("AppPicker", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("renders all apps when category=All", () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(3);
  });

  it("filters by category chip", async () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    await w.find("[data-test='cat-ML / AI']").trigger("click");
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(1);
  });

  it("filters by search text within current category", async () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    await w.find("input[data-test='app-search']").setValue("NAMD");
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(1);
  });

  it("clicking a tile picks the app via the store", async () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    await w.find("[data-test='app-tile-namd']").trigger("click");
    expect(useLaunchStore().draft.app_id).toBe("namd");
  });
});
