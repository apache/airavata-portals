import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ProjectListContainer from "./containers/ProjectListContainer.vue";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("project-list");
const initialProjectsData = el?.dataset.projectsData
  ? JSON.parse(el.dataset.projectsData)
  : null;

const App = {
  render() {
    return h(components.MainLayout, () => [
      h(ProjectListContainer, { initialProjectsData }),
    ]);
  },
};

entry(App).mount("#project-list");
