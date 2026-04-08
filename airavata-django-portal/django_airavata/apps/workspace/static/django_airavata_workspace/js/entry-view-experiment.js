import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import { mapActions } from "vuex";
import ExperimentSummary from "./components/experiment/ExperimentSummary.vue";
import createStore from "./store";

entry(({ createApp }) => {
  const store = createStore();
  const app = createApp({
    async beforeMount() {
      const fullExperimentData = JSON.parse(
        this.$el.dataset.fullExperimentData
      );
      this.setInitialFullExperimentData({ fullExperimentData });
      if ("launching" in this.$el.dataset) {
        const launching = JSON.parse(this.$el.dataset.launching);
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
