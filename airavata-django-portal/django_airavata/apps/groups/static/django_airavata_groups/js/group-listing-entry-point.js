import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GroupsManageContainer from "./containers/GroupsManageContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(GroupsManageContainer),
      });
    },
  });
  app.mount("#group-list");
});
