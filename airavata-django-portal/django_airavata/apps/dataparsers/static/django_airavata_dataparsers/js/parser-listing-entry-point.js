import { h } from "vue";
// Deep imports (not the `index.js` barrel) so this page-level bundle pulls in
// only the layout it renders. Importing the `components` barrel would also bundle
// the shared `Uppy` component, whose `@uppy/status-bar/dist/style.min.css` import
// is not resolvable under the package's `exports` field (these pages never use
// the uploader). See TODO(vue3-migration) note in the migration report.
import entry from "django-airavata-common-ui/js/entry";
import MainLayout from "django-airavata-common-ui/js/components/MainLayout.vue";
import ParsersManageContainer from "./containers/ParsersManageContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles (loads the shared
// common bundle's CSS). The shadcn-vue UI components are registered globally by
// common's entry(), so templates use <Button>/<Card>/<Input>/... with no imports.
import "django-airavata-common-ui/css/app.css";

const App = {
  render() {
    return h(MainLayout, () => [h(ParsersManageContainer)]);
  },
};

entry(App).mount("#parsers-manage");
