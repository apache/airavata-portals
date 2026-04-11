import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import GatewaySettingsContainer from "./containers/GatewaySettingsContainer.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(GatewaySettingsContainer),
      });
    },
  });
  app.mount("#gateway-settings");
});
