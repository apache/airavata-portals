import { entry } from "django-airavata-common-ui";
import GroupCreateContainer from "./containers/GroupCreateContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles.
import "django-airavata-common-ui/css/app.css";

// Read data-* attributes before mounting: Vue 3 replaces the element's contents.
const mountEl = document.getElementById("group-create");
const next = mountEl?.dataset.next || "/groups/";

// The container renders its own <main-layout> (page header + gutter), so it is
// mounted directly here instead of being wrapped again.
entry(GroupCreateContainer, { next }).mount("#group-create");
