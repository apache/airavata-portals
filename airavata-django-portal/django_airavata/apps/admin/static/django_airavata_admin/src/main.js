import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import FlatPickr from "vue-flatpickr-component";
import App from "./App.vue";
import router from "./router";

import "flatpickr/dist/flatpickr.css";
import createStore from "./store";

// Root render: wrap <App> inside the shared MainLayout (Vue 3 has no global Vue,
// so the layout/app composition that used to live in `new Vue({ render })` moves
// here as an inline root render function).
const Root = {
  render() {
    return h(components.MainLayout, () => [h(App)]);
  },
};

const app = entry(Root);
app.use(router);
app.use(createStore());
// vue-flatpickr-component v12 registers as a global component (was Vue.use in v8).
app.component("flat-pickr", FlatPickr);
app.mount("#app");
