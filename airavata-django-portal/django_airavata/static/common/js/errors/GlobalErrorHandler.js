import { errors } from "django-airavata-api";

class GlobalErrorHandler {
  init() {
    console.log("Initializing GlobalErrorHandler...");  
    window.onerror = this.handleGlobalError;
  }

  handleGlobalError(msg, url, lineNo, columnNo, error) {
    errors.UnhandledErrorDispatcher.reportError({
      message: msg,
      error: error,
      details: {
        url,
        lineNo,
        columnNo,
      },
    });

    return false;
  }

  // Vue 3 app-level error handler. There is no global Vue config in Vue 3, so this
  // is wired up per app via `app.config.errorHandler` in the common entry() helper.
  vueGlobalErrorHandler(err, instance, info) {
    console.log("Vue Global Error Handler", err, instance, info);  
    errors.UnhandledErrorDispatcher.reportError({
      message: err.message,
      error: err,
      details: info,
    });
  }
}

export default new GlobalErrorHandler();
