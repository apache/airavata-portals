import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import EditExperimentContainer from "./containers/EditExperimentContainer.vue";
import "../../scss/styles.scss";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        experimentId: null,
      };
    },
    beforeMount() {
      this.experimentId = this.$el.dataset.experimentId;
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(EditExperimentContainer, {
            experimentId: this.experimentId,
          }),
      });
    },
  });
  app.mount("#edit-experiment");
});
