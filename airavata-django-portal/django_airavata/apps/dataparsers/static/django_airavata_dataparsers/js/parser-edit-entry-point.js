import { h } from "vue";
// Deep imports (not the `index.js` barrel) so this page-level bundle pulls in
// only the layout it renders. Importing the `components` barrel would also bundle
// the shared `Uppy` component, whose `@uppy/status-bar/dist/style.min.css` import
// is not resolvable under the package's `exports` field (these pages never use
// the uploader). See TODO(vue3-migration) note in the migration report.
import entry from "django-airavata-common-ui/js/entry";
import MainLayout from "django-airavata-common-ui/js/components/MainLayout.vue";
import ParserEditContainer from "./containers/ParserEditContainer.vue";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("edit-parser");
const parserId = el?.dataset.parserId ?? null;

const App = {
  render() {
    return h(MainLayout, () => [h(ParserEditContainer, { parserId })]);
  },
};

entry(App).mount("#edit-parser");
