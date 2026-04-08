import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import { createRouter, createWebHistory } from "vue-router";
import VueFlatPickr from "vue-flatpickr-component";
import App from "./App.vue";
import { routes } from "./router";
import createStore from "./store";

import "flatpickr/dist/flatpickr.css";

entry(({ createApp }) => {
  const router = createRouter({
    history: createWebHistory("/admin/"),
    routes,
  });

  const store = createStore();

  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(App),
      });
    },
  });

  app.use(router);
  app.use(store);
  app.use(VueFlatPickr);

  app.mount("#app");
});
