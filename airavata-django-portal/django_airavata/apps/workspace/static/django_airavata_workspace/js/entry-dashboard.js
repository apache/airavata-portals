import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import DashboardContainer from "./containers/DashboardContainer.vue";
import RecentExperimentsContainer from "./containers/RecentExperimentsContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        viewAllExperiments: null,
        username: null,
      };
    },
    beforeMount() {
      this.viewAllExperiments = this.$el.dataset.viewAllExperiments;
      this.username = this.$el.dataset.username;
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
