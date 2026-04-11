import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import EditProjectContainer from "./containers/EditProjectContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("edit-project");
  const projectId = el ? el.dataset.projectId || null : null;
  const app = createApp({
    data() {
      return {
        projectId,
      };
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(EditProjectContainer, {
            projectId: this.projectId,
          }),
      });
    },
  });
  app.mount("#edit-project");
});
