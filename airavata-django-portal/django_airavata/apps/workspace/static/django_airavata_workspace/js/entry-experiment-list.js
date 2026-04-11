import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ExperimentListContainer from "./containers/ExperimentListContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("experiment-list");
  const experimentsData = el && el.dataset.experimentsData
    ? JSON.parse(el.dataset.experimentsData)
    : null;
  const projectId = el ? el.dataset.projectId : null;
  const breadcrumbs = el && el.dataset.breadcrumbs
    ? JSON.parse(el.dataset.breadcrumbs)
    : [];

  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(ExperimentListContainer, {
            initialExperimentsData: experimentsData,
            projectId,
            breadcrumbs,
          }),
      });
    },
  });
  app.mount("#experiment-list");
});
