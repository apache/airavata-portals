import { createApp } from "vue";
import GlobalErrorHandler from "./errors/GlobalErrorHandler";
import * as UI from "./components/ui";

// Tailwind v4 + shadcn-vue design tokens and base styles.
import "../css/app.css";

GlobalErrorHandler.init();

// Register every shadcn-vue UI component (Button, Card, Input, Dialog, ...) globally
// so templates can use the <Component> / <component> tags without per-file imports —
// the same global-availability contract the portal relied on before. The barrel also
// exports cva variant helpers (buttonVariants, ...) which are plain functions and are
// skipped here.
function registerUI(app) {
  for (const [name, exported] of Object.entries(UI)) {
    if (/^[A-Z]/.test(name) && exported && typeof exported === "object") {
      app.component(name, exported);
    }
  }
}

/**
 * Common entry point. Creates a Vue 3 app for `rootComponent` with the shared
 * shadcn-vue UI components registered globally and the portal's error handler
 * wired up. Callers add their own router/store and mount the returned app:
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
  registerUI(app);
  return app;
}
