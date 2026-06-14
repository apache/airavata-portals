import { h } from "vue";
import { createPinia } from "pinia";
import { components, entry } from "django-airavata-common-ui";
// Tailwind v4 + shadcn-vue design tokens and base styles (shared with common).
import "django-airavata-common-ui/css/app.css";
import ExperimentSummary from "./components/experiment/ExperimentSummary.vue";
import { useViewExperimentStore } from "./store";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("view-experiment");
const fullExperimentData = JSON.parse(el.dataset.fullExperimentData);
const launching =
  "launching" in el.dataset ? JSON.parse(el.dataset.launching) : null;

const App = {
  render() {
    return h(components.MainLayout, () => [h(ExperimentSummary)]);
  },
  beforeMount() {
    const store = useViewExperimentStore();
    store.setInitialFullExperimentData({ fullExperimentData });
    if (launching !== null) {
      store.setLaunching({ launching });
    }
  },
};

const app = entry(App);
app.use(createPinia());
app.mount("#view-experiment");
