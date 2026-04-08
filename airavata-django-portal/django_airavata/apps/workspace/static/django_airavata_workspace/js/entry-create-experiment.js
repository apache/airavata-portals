import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import CreateExperimentContainer from "./containers/CreateExperimentContainer.vue";
import "../../scss/styles.scss";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        appModuleId: null,
        userInputValues: null,
        experimentDataDir: null,
      };
    },
    beforeMount() {
      if (this.$el.dataset.appModuleId) {
        this.appModuleId = this.$el.dataset.appModuleId;
      }
      if (this.$el.dataset.userInputValues) {
        this.userInputValues = JSON.parse(this.$el.dataset.userInputValues);
      }
      if (this.$el.dataset.experimentDataDir) {
        this.experimentDataDir = this.$el.dataset.experimentDataDir;
      }
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(CreateExperimentContainer, {
            appModuleId: this.appModuleId,
            userInputValues: this.userInputValues,
            experimentDataDir: this.experimentDataDir,
          }),
      });
    },
  });
  app.mount("#create-experiment");
});
