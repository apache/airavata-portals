import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ProjectListContainer from "./containers/ProjectListContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("project-list");
  const projectsData = el && el.dataset.projectsData
    ? JSON.parse(el.dataset.projectsData)
    : null;
  const app = createApp({
    data() {
      return {
        projectsData,
      };
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(ProjectListContainer, {
            initialProjectsData: this.projectsData,
          }),
      });
    },
  });
  app.mount("#project-list");
});
