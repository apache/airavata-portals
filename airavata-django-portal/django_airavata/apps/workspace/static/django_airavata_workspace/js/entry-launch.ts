import { h } from "vue";
// @ts-expect-error — django-airavata-common-ui still ships untyped exports
import { components, entry } from "django-airavata-common-ui";
import LaunchContainer from "./containers/LaunchContainer.vue";

entry(({ createApp }: { createApp: (options: object) => { mount: (sel: string) => void } }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(LaunchContainer),
      });
    },
  });
  app.mount("#launch-app");
});
