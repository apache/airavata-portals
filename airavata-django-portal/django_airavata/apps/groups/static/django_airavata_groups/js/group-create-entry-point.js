import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GroupCreateContainer from "./containers/GroupCreateContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles.
import "django-airavata-common-ui/css/app.css";

// Read data-* attributes before mounting: Vue 3 replaces the element's contents.
const mountEl = document.getElementById("group-create");
const next = mountEl?.dataset.next || "/groups/";

const App = {
  render() {
    return h(components.MainLayout, () => [h(GroupCreateContainer, { next })]);
  },
};

entry(App).mount("#group-create");
