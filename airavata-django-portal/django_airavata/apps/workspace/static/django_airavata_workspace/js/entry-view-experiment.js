import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import { mapActions } from "vuex";
import ExperimentSummary from "./components/experiment/ExperimentSummary.vue";
import createStore from "./store";

entry(({ createApp }) => {
  const el = document.getElementById("view-experiment");
  const fullExperimentData = el && el.dataset.fullExperimentData
    ? JSON.parse(el.dataset.fullExperimentData)
    : null;
  const launching = el && "launching" in el.dataset
    ? JSON.parse(el.dataset.launching)
    : null;
  const store = createStore();
  const app = createApp({
    beforeMount() {
      if (fullExperimentData) {
        this.setInitialFullExperimentData({ fullExperimentData });
      }
      if (launching !== null) {
        this.setLaunching({ launching });
      }
    },
    methods: {
      ...mapActions("viewExperiment", [
        "setInitialFullExperimentData",
        "setLaunching",
      ]),
    },
    render() {
      return h(components.MainLayout, null, {
        default: () => h(ExperimentSummary),
      });
    },
  });
  app.use(store);
  app.mount("#view-experiment");
});
