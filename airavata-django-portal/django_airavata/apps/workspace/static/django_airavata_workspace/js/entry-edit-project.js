import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import EditProjectContainer from "./containers/EditProjectContainer.vue";

// Expect a template with id "edit-project" and project-id data attribute
//
//   <div id="edit-project" data-project-id="..projectID.."/>
//
// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("edit-project");
const projectId = el?.dataset.projectId ?? null;

const App = {
  render() {
    return h(components.MainLayout, () => [
      h(EditProjectContainer, { projectId }),
    ]);
  },
};

entry(App).mount("#edit-project");
