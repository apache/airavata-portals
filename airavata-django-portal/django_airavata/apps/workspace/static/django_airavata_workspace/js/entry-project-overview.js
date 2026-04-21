import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ProjectOverviewContainer from "./containers/ProjectOverviewContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("project-overview");
  const projectId = el ? el.dataset.projectId : null;
  const projectName = el ? el.dataset.projectName : "";
  const breadcrumbs = el && el.dataset.breadcrumbs ? JSON.parse(el.dataset.breadcrumbs) : [];

  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(ProjectOverviewContainer, {
            projectId,
            projectName,
            breadcrumbs,
          }),
      });
    },
  });
  app.mount("#project-overview");
});
