import { describe, test, expect } from "vitest";
import { mount } from "@vue/test-utils";
import ProjectListItem from "@/components/project/ProjectListItem.vue";

describe("ProjectListItem", () => {
  const project = {
    projectID: "proj-1",
    name: "My Project",
    description: "Sample project",
    creation_time: new Date(Date.now() - 3 * 3600_000).toISOString(),
    owner: "testuser",
  };

  test("renders the project name", () => {
    const wrapper = mount(ProjectListItem, { props: { project } });
    expect(wrapper.text()).toContain("My Project");
  });

  test("renders a relative creation time", () => {
    const wrapper = mount(ProjectListItem, { props: { project } });
    // Exact phrasing depends on Intl.RelativeTimeFormat locale output.
    expect(wrapper.text()).toMatch(/hours? ago/);
  });
});
