import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import CreateExperimentContainer from "./containers/CreateExperimentContainer.vue";
// Tailwind v4 + shadcn-vue design tokens and base styles (shared with common).
import "django-airavata-common-ui/css/app.css";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("create-experiment");
const appModuleId = el?.dataset.appModuleId ?? null;
const userInputValues = el?.dataset.userInputValues
  ? JSON.parse(el.dataset.userInputValues)
  : null;
const experimentDataDir = el?.dataset.experimentDataDir ?? null;

const App = {
  render() {
    return h(components.MainLayout, () => [
      h(CreateExperimentContainer, {
        appModuleId,
        userInputValues,
        experimentDataDir,
      }),
    ]);
  },
};

entry(App).mount("#create-experiment");
