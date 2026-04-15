import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ApplicationEditorContainer from "./containers/ApplicationEditorContainer.vue";

entry(({ createApp }) => {
  const appEl = document.getElementById("application-editor");
  const appModuleId = appEl ? appEl.dataset.appModuleId : null;

  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(ApplicationEditorContainer, {
            appModuleId: appModuleId || null,
          }),
      });
    },
  });
  app.mount("#application-editor");
});
