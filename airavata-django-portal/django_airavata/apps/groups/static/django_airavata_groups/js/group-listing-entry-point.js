import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GroupsManageContainer from "./containers/GroupsManageContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles.
import "django-airavata-common-ui/css/app.css";

const App = {
  render() {
    return h(components.MainLayout, () => [h(GroupsManageContainer)]);
  },
};

entry(App).mount("#group-list");
