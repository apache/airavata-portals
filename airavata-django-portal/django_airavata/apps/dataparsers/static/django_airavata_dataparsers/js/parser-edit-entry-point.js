import { h } from "vue";
// Deep import (not the `index.js` barrel) so this page-level bundle pulls in only
// what it renders. Importing the `components` barrel would also bundle the shared
// `Uppy` component, whose `@uppy/status-bar/dist/style.min.css` import is not
// resolvable under the package's `exports` field (these pages never use the
// uploader). See TODO(vue3-migration) note in the migration report.
import entry from "django-airavata-common-ui/js/entry";
import ParserEditContainer from "./containers/ParserEditContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles (loads the shared
// common bundle's CSS). The shadcn-vue UI components are registered globally by
// common's entry(), so templates use <Button>/<Card>/<Input>/... with no imports.
import "django-airavata-common-ui/css/app.css";

// Read the mount element's data-* attributes before mounting; Vue 3 replaces the
// element's contents on mount.
const el = document.getElementById("edit-parser");
const parserId = el?.dataset.parserId ?? null;

// The container renders its own MainLayout (page title/subtitle + actions).
const App = {
  render() {
    return h(ParserEditContainer, { parserId });
  },
};

entry(App).mount("#edit-parser");
