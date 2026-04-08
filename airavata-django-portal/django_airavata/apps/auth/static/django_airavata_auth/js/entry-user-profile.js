import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import UserProfileContainer from "./containers/UserProfileContainer.vue";
import createStore from "./store";

entry(({ createApp }) => {
  const store = createStore();
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(UserProfileContainer),
      });
    },
  });
  app.use(store);
  app.mount("#user-profile");
});
