import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ComputeContainer from "./containers/ComputeContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(ComputeContainer),
      });
    },
  });
  app.mount("#compute");
});
