import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ComputeDetailContainer from "./containers/ComputeDetailContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("compute-detail");
  const computeResourceId = el ? el.dataset.computeResourceId : null;
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(ComputeDetailContainer, { computeResourceId }),
      });
    },
  });
  app.mount("#compute-detail");
});
