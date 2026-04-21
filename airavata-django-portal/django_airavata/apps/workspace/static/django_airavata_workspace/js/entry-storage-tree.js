import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import StorageTreeContainer from "./containers/StorageTreeContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("storage-tree");
  const storageResourceId = el ? el.dataset.storageResourceId : null;
  const storagePath = el ? el.dataset.storagePath || "" : "";
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(StorageTreeContainer, { storageResourceId, initialPath: storagePath }),
      });
    },
  });
  app.mount("#storage-tree");
});
