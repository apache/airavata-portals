import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import CreateExperimentContainer from "./containers/CreateExperimentContainer.vue";
import "../../scss/styles.scss";

entry(({ createApp }) => {
  const el = document.getElementById("create-experiment");
  const appModuleId = el ? el.dataset.appModuleId || null : null;
  const userInputValues =
    el && el.dataset.userInputValues ? JSON.parse(el.dataset.userInputValues) : null;
  const experimentDataDir = el ? el.dataset.experimentDataDir || null : null;
  const app = createApp({
    data() {
      return {
        appModuleId,
        userInputValues,
        experimentDataDir,
      };
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
