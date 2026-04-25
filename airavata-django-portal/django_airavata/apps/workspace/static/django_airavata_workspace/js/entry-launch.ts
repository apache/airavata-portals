import { createApp } from "vue";
import { createPinia } from "pinia";
import LaunchContainer from "./containers/LaunchContainer.vue";

const root = document.getElementById("launch-app");
if (root) {
  const app = createApp(LaunchContainer);
  app.use(createPinia());
  app.mount(root);
}
