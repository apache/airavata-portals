import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import { createRouter, createWebHistory } from "vue-router";
import UserStorageContainer from "./containers/UserStorageContainer.vue";
import UserStoragePathViewer from "./components/storage/UserStoragePathViewer.vue";

const routes = [
  {
    path: "/:pathMatch(.*)*",
    component: UserStoragePathViewer,
  },
];

entry(({ createApp }) => {
  const router = createRouter({
    history: createWebHistory("/workspace/storage"),
    routes,
  });

  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(UserStorageContainer),
      });
    },
  });
  app.use(router);
  app.mount("#user-storage");
});
