import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ExperimentListContainer from "./containers/ExperimentListContainer.vue";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("experiment-list");
const initialExperimentsData = el?.dataset.experimentsData
  ? JSON.parse(el.dataset.experimentsData)
  : null;

const App = {
  render() {
    return h(components.MainLayout, () => [
      h(ExperimentListContainer, { initialExperimentsData }),
    ]);
  },
};

entry(App).mount("#experiment-list");
