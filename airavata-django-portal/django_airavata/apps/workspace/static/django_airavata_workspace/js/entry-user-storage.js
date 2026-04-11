import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import UserStorageContainer from "./containers/UserStorageContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(UserStorageContainer),
      });
    },
  });
  app.mount("#user-storage");
});
