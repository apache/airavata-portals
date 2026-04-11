import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";

// Import the CredentialStoreDashboard from the admin app
import CredentialStoreDashboard from "../../../../admin/static/django_airavata_admin/src/components/dashboards/CredentialStoreDashboard.vue";

entry(({ createApp }) => {
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(CredentialStoreDashboard),
      });
    },
  });
  app.mount("#credentials");
});
