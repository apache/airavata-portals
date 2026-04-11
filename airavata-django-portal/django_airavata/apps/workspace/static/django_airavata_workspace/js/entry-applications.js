import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import DashboardContainer from "./containers/DashboardContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(DashboardContainer),
      });
    },
  });
  app.mount("#applications");
});
