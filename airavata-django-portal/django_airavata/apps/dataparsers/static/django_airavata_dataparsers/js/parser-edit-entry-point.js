import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ParserEditContainer from "./containers/ParserEditContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        parserId: null,
      };
    },
    beforeMount() {
      if (this.$el.dataset.parserId) {
        this.parserId = this.$el.dataset.parserId;
      }
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(ParserEditContainer, {
            parserId: this.parserId,
          }),
      });
    },
  });
  app.mount("#edit-parser");
});
