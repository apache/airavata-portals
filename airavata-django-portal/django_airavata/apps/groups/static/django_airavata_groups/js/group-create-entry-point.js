import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GroupCreateContainer from "./containers/GroupCreateContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        next: "/resources/sharing/",
      };
    },
    beforeMount() {
      if (this.$el.dataset.next) {
        this.next = this.$el.dataset.next;
      }
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(GroupCreateContainer, {
            next: this.next,
          }),
      });
    },
  });
  app.mount("#group-create");
});
