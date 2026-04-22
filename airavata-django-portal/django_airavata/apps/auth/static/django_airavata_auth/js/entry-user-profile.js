import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import UserProfileContainer from "./containers/UserProfileContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(UserProfileContainer),
      });
    },
  });
  app.mount("#user-profile");
});
