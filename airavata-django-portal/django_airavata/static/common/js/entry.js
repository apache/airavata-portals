import { createApp as vueCreateApp } from "vue";
import { createPinia } from "pinia";
import GlobalErrorHandler from "./errors/GlobalErrorHandler";

GlobalErrorHandler.init();

/**
 * Common entry point function. Sets up common entry point functionality and
 * then calls the passed function with a createApp factory that auto-installs
 * the global error handler and a shared Pinia instance.
 *
 * Pinia coexists with Vuex (M3). Consumer migration to Pinia stores is M4.
 *
 * @param {Function} entryPointFunction - receives { createApp }
 */
export default function entry(entryPointFunction) {
  const pinia = createPinia();

  function createApp(options) {
    const app = vueCreateApp(options);
    GlobalErrorHandler.installVueErrorHandler(app);
    app.use(pinia);
    return app;
  }

  entryPointFunction({ createApp });
}
