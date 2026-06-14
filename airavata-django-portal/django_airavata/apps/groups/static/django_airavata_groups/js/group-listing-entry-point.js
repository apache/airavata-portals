import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GroupsManageContainer from "./containers/GroupsManageContainer.vue";

const App = {
  render() {
    return h(components.MainLayout, () => [h(GroupsManageContainer)]);
  },
};

entry(App).mount("#group-list");
