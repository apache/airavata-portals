import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import DatasetsContainer from "./containers/DatasetsContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("datasets");
  const projectId = el ? el.dataset.projectId : null;
  const breadcrumbs = el && el.dataset.breadcrumbs ? JSON.parse(el.dataset.breadcrumbs) : [];

  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(DatasetsContainer, {
            projectId,
            breadcrumbs,
          }),
      });
    },
  });
  app.mount("#datasets");
});
