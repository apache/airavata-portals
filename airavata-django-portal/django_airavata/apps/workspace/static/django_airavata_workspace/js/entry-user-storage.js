import { h } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import { components, entry } from "django-airavata-common-ui";
// Tailwind v4 + shadcn-vue design tokens and base styles (shared with common).
import "django-airavata-common-ui/css/app.css";
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

// Storage is a router-view page, so its consistent header lives here in the
// entry's MainLayout rather than in a single root component.
const App = {
  render() {
    return h(
      components.MainLayout,
      {
        title: "Storage",
        subtitle: "Browse, upload, and manage your files.",
      },
      () => [h(UserStorageContainer)],
    );
  },
};

const app = entry(App);
app.use(router);
app.mount("#user-storage");
