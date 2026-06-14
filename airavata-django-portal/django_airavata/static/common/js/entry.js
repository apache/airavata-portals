import { createApp } from "vue";
import { createBootstrap } from "bootstrap-vue-next";
import GlobalErrorHandler from "./errors/GlobalErrorHandler";

// bootstrap-vue-next styles. Bootstrap's own CSS is loaded globally on the page
// (see main.js), so only the component-library CSS is needed here.
import "bootstrap-vue-next/dist/bootstrap-vue-next.css";

GlobalErrorHandler.init();

/**
 * Common entry point. Creates a Vue 3 app for `rootComponent` pre-configured with
 * the portal's shared plugins (BootstrapVueNext, which globally registers the
 * `<b-*>` components and `v-b-*` directives). Replaces the Vue 2
 * `entry(fn => fn(Vue))` global pattern — Vue 3 has no global Vue, so callers add
 * their own router/store/components on the returned app and mount it themselves:
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
  return app;
}
