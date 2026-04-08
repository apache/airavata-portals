import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ParsersManageContainer from "./containers/ParsersManageContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(ParsersManageContainer),
      });
    },
  });
  app.mount("#parsers-manage");
});
