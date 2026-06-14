import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GroupEditContainer from "./containers/GroupEditContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles.
import "django-airavata-common-ui/css/app.css";

// Read data-* attributes before mounting: Vue 3 replaces the element's contents.
const mountEl = document.getElementById("group-edit");
const groupId = mountEl?.dataset.groupId || null;
const next = mountEl?.dataset.next || "/groups/";

const App = {
  render() {
    return h(components.MainLayout, () => [
      h(GroupEditContainer, { groupId, next }),
    ]);
  },
};

entry(App).mount("#group-edit");
