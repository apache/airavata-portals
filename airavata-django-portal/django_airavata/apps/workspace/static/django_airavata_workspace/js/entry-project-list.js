import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ProjectListContainer from "./containers/ProjectListContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        projectsData: null,
      };
    },
    beforeMount() {
      if (this.$el.dataset.projectsData) {
        this.projectsData = JSON.parse(this.$el.dataset.projectsData);
      }
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(ProjectListContainer, {
            initialProjectsData: this.projectsData,
          }),
      });
    },
  });
  app.mount("#project-list");
});
