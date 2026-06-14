import { h } from "vue";
import { TooltipProvider } from "django-airavata-common-ui/js/components/ui";
import { entry } from "django-airavata-common-ui";
import FlatPickr from "vue-flatpickr-component";
import App from "./App.vue";
import router from "./router";

import "django-airavata-common-ui/css/app.css";
import "flatpickr/dist/flatpickr.css";
import createStore from "./store";

// Root render: a TooltipProvider wraps the whole app so the shadcn-vue <Tooltip>
// instances used across the admin app (and in shared common components like
// ClipboardCopyLink/ShareButton) have the provider context reka-ui requires.
// Each routed page renders its own <MainLayout> so it can supply a page-specific
// title/subtitle/actions header (the consistent page chrome), rather than sharing
// one title-less layout here.
const Root = {
  render() {
    return h(TooltipProvider, { delayDuration: 150 }, () => [h(App)]);
  },
};

const app = entry(Root);
app.use(router);
app.use(createStore());
// vue-flatpickr-component v12 registers as a global component (was Vue.use in v8).
app.component("flat-pickr", FlatPickr);
app.mount("#app");
