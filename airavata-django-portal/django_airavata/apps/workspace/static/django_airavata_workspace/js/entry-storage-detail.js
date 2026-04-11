import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import StorageDetailContainer from "./containers/StorageDetailContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("storage-detail");
  const storageResourceId = el ? el.dataset.storageResourceId : null;
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(StorageDetailContainer, { storageResourceId }),
      });
    },
  });
  app.mount("#storage-detail");
});
