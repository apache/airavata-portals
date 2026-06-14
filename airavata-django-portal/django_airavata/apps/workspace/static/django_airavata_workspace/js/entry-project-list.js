import { h } from "vue";
import { entry } from "django-airavata-common-ui";
// Tailwind v4 + shadcn-vue design tokens and base styles (shared with common).
import "django-airavata-common-ui/css/app.css";
import ProjectListContainer from "./containers/ProjectListContainer.vue";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("project-list");
const initialProjectsData = el?.dataset.projectsData
  ? JSON.parse(el.dataset.projectsData)
  : null;

// The container renders its own MainLayout (page header + actions slot).
const App = {
  render() {
    return h(ProjectListContainer, { initialProjectsData });
  },
};

entry(App).mount("#project-list");
