import { h } from "vue";
import { entry } from "django-airavata-common-ui";
// Tailwind v4 + shadcn-vue design tokens and base styles (shared with common).
import "django-airavata-common-ui/css/app.css";
import EditProjectContainer from "./containers/EditProjectContainer.vue";

// Expect a template with id "edit-project" and project-id data attribute
//
//   <div id="edit-project" data-project-id="..projectID.."/>
//
// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("edit-project");
const projectId = el?.dataset.projectId ?? null;

// The container renders its own MainLayout (page header + actions slot).
const App = {
  render() {
    return h(EditProjectContainer, { projectId });
  },
};

entry(App).mount("#edit-project");
