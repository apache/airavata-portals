import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ExperimentSummary from "./components/experiment/ExperimentSummary.vue";
import { useExperimentStore } from "django-airavata-common-ui/js/stores/experiment";

entry(({ createApp }) => {
  const el = document.getElementById("view-experiment");
  const fullExperimentData =
    el && el.dataset.fullExperimentData ? JSON.parse(el.dataset.fullExperimentData) : null;
  const launching = el && "launching" in el.dataset ? JSON.parse(el.dataset.launching) : null;
  const app = createApp({
    setup() {
      const experimentStore = useExperimentStore();
      return { experimentStore };
    },
    beforeMount() {
      if (fullExperimentData) {
        this.experimentStore.setInitialFullExperimentData({ fullExperimentData });
      }
      if (launching !== null) {
        this.experimentStore.setLaunching({ launching });
      }
    },
    render() {
      return h(components.MainLayout, null, {
        default: () => h(ExperimentSummary),
      });
    },
  });
  app.mount("#view-experiment");
});
