import { h } from "vue";
import { TooltipProvider } from "django-airavata-common-ui/js/components/ui";
import { components, entry } from "django-airavata-common-ui";
import FlatPickr from "vue-flatpickr-component";
import App from "./App.vue";
import router from "./router";

import "django-airavata-common-ui/css/app.css";
import "flatpickr/dist/flatpickr.css";
import createStore from "./store";

// Root render: wrap <App> inside the shared MainLayout (Vue 3 has no global Vue,
// so the layout/app composition that used to live in `new Vue({ render })` moves
// here as an inline root render function). A TooltipProvider wraps everything so
// the shadcn-vue <Tooltip> instances used across the admin app (and in shared
// common components like ClipboardCopyLink/ShareButton) have the provider context
// reka-ui requires.
const Root = {
  render() {
    return h(TooltipProvider, { delayDuration: 150 }, () => [
      h(components.MainLayout, () => [h(App)]),
    ]);
  },
};

const app = entry(Root);
app.use(router);
app.use(createStore());
// vue-flatpickr-component v12 registers as a global component (was Vue.use in v8).
app.component("flat-pickr", FlatPickr);
app.mount("#app");
