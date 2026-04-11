import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GroupEditContainer from "./containers/GroupEditContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    data() {
      return {
        groupId: null,
        next: "/resources/sharing/",
      };
    },
    beforeMount() {
      if (this.$el.dataset.groupId) {
        this.groupId = this.$el.dataset.groupId;
      }
      if (this.$el.dataset.next) {
        this.next = this.$el.dataset.next;
      }
    },
    render() {
      return h(components.MainLayout, null, {
        default: () =>
          h(GroupEditContainer, {
            groupId: this.groupId,
            next: this.next,
          }),
      });
    },
  });
  app.mount("#group-edit");
});
