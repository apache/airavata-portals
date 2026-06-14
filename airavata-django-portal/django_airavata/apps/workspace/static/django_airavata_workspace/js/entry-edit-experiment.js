import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import EditExperimentContainer from "./containers/EditExperimentContainer.vue";
import "../../scss/styles.scss";

// Expect a template with id "edit-experiment" and experiment-id data attribute
//
//   <div id="edit-experiment" data-experiment-id="..expid.."/>
//
// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("edit-experiment");
const experimentId = el?.dataset.experimentId ?? null;

const App = {
  render() {
    return h(components.MainLayout, () => [
      h(EditExperimentContainer, { experimentId }),
    ]);
  },
};

entry(App).mount("#edit-experiment");
