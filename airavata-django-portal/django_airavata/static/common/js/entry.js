import { createApp } from "vue";
import { createBootstrap } from "bootstrap-vue-next";
import * as BootstrapVueNext from "bootstrap-vue-next";
import GlobalErrorHandler from "./errors/GlobalErrorHandler";

// bootstrap-vue-next styles. Bootstrap's own CSS is loaded globally on the page
// (see main.js), so only the component-library CSS is needed here.
import "bootstrap-vue-next/dist/bootstrap-vue-next.css";

GlobalErrorHandler.init();

// Unlike Vue 2's `Vue.use(BootstrapVue)`, bootstrap-vue-next's createBootstrap()
// plugin only installs directives/composables/defaults — it does NOT globally
// register the components. The library expects per-file imports or the
// unplugin-vue-components resolver. The portal's templates use bare <b-*> tags
// everywhere (no per-file imports), so register every exported B* component
// globally once, here, to preserve that contract for all consuming apps.
function registerAllComponents(app) {
  for (const [name, exported] of Object.entries(BootstrapVueNext)) {
    // Component export names are PascalCase starting with `B` + an uppercase
    // letter (BButton, BFormInput, ...). This excludes createBootstrap, the
    // *Plugin helpers, composables (use*), and BootstrapVueNextResolver.
    if (!/^B[A-Z]/.test(name)) continue;
    if (exported && (typeof exported === "object" || typeof exported === "function")) {
      app.component(name, exported);
    }
  }
}

/**
 * Common entry point. Creates a Vue 3 app for `rootComponent` pre-configured with
 * the portal's shared plugins (BootstrapVueNext directives + every <b-*>
 * component registered globally). Replaces the Vue 2 `entry(fn => fn(Vue))` global
 * pattern — Vue 3 has no global Vue, so callers add their own router/store/
 * components on the returned app and mount it themselves:
 *
 *   entry(RootComponent).use(router).mount("#root");
 *
 * @param {object} rootComponent the root Vue component
 * @param {object} [rootProps] optional props for the root component
 * @returns {import("vue").App} the configured (unmounted) Vue application
 */
export default function entry(rootComponent, rootProps) {
  const app = createApp(rootComponent, rootProps);
  app.config.errorHandler = GlobalErrorHandler.vueGlobalErrorHandler;
  app.use(createBootstrap());
  registerAllComponents(app);
  return app;
}
