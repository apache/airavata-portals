import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
// Tailwind v4 + shadcn-vue design tokens and base styles (shared with common).
import "django-airavata-common-ui/css/app.css";
import DashboardContainer from "./containers/DashboardContainer.vue";
import RecentExperimentsContainer from "./containers/RecentExperimentsContainer.vue";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("dashboard");
const viewAllExperiments = el?.dataset.viewAllExperiments ?? null;
const username = el?.dataset.username ?? null;

const App = {
  render() {
    return h(
      components.MainLayout,
      {},
      {
        default: () => [h(DashboardContainer)],
        sidebar: () => [
          h(RecentExperimentsContainer, { viewAllExperiments, username }),
        ],
      },
    );
  },
};

entry(App).mount("#dashboard");
