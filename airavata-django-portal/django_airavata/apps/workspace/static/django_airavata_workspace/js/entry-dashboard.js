import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import DashboardContainer from "./containers/DashboardContainer.vue";
import RecentExperimentsContainer from "./containers/RecentExperimentsContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("dashboard");
  const viewAllExperiments = el ? el.dataset.viewAllExperiments : null;
  const username = el ? el.dataset.username : null;
  const app = createApp({
    data() {
      return { viewAllExperiments, username };
    },
    render() {
      return h(components.MainLayout, null, {
        default: () => h(DashboardContainer),
        sidebar: () =>
          h(RecentExperimentsContainer, {
            viewAllExperiments: this.viewAllExperiments,
            username: this.username,
          }),
      });
    },
  });
  app.mount("#dashboard");
});
