import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import EditProjectContainer from "./containers/EditProjectContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        projectId: null,
      };
    },
    beforeMount() {
      this.projectId = this.$el.dataset.projectId;
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
