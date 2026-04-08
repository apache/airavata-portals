import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ParserDetailsContainer from "./containers/ParserDetailsContainer.vue";

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
          h(ParserDetailsContainer, {
            parserId: this.parserId,
          }),
      });
    },
  });
  app.mount("#parser-details");
});
