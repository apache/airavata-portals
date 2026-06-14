import { h } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import { components, entry } from "django-airavata-common-ui";
import UserStorageContainer from "./containers/UserStorageContainer.vue";
import UserStoragePathViewer from "./components/storage/UserStoragePathViewer.vue";

const routes = [
  {
    // Vue Router 4/5 catch-all replaces the Vue Router 3 `path: "*"` wildcard.
    path: "/:pathMatch(.*)*",
    component: UserStoragePathViewer,
  },
];
const router = createRouter({
  history: createWebHistory("/workspace/storage"),
  routes,
});

const App = {
  render() {
    return h(components.MainLayout, () => [h(UserStorageContainer)]);
  },
};

const app = entry(App);
app.use(router);
app.mount("#user-storage");
