import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import EditExperimentContainer from "./containers/EditExperimentContainer.vue";
import "../../scss/styles.scss";

entry(({ createApp }) => {
  const el = document.getElementById("edit-experiment");
  const experimentId = el ? el.dataset.experimentId || null : null;
  const app = createApp({
    data() {
      return {
        experimentId,
      };
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
