import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ExperimentListContainer from "./containers/ExperimentListContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        experimentsData: null,
      };
    },
    beforeMount() {
      if (this.$el.dataset.experimentsData) {
        this.experimentsData = JSON.parse(this.$el.dataset.experimentsData);
      }
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(ExperimentListContainer, {
            initialExperimentsData: this.experimentsData,
          }),
      });
    },
  });
  app.mount("#experiment-list");
});
