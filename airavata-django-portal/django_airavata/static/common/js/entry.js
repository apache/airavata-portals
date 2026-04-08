import { createApp as vueCreateApp } from "vue";
import GlobalErrorHandler from "./errors/GlobalErrorHandler";

GlobalErrorHandler.init();

/**
 * Common entry point function. Sets up common entry point functionality and
 * then calls the passed function with a createApp factory that auto-installs
 * the global error handler.
 *
 * @param {Function} entryPointFunction - receives { createApp }
 */
export default function entry(entryPointFunction) {
  function createApp(options) {
    const app = vueCreateApp(options);
    GlobalErrorHandler.installVueErrorHandler(app);
    return app;
  }

  entryPointFunction({ createApp });
}
