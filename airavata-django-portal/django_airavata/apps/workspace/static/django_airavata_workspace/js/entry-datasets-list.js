import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import DatasetsListContainer from "./containers/DatasetsListContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(DatasetsListContainer),
      });
    },
  });
  app.mount("#workspace-datasets");
});
