import { entry } from "django-airavata-common-ui";
import GroupEditContainer from "./containers/GroupEditContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles.
import "django-airavata-common-ui/css/app.css";

// Read data-* attributes before mounting: Vue 3 replaces the element's contents.
const mountEl = document.getElementById("group-edit");
const groupId = mountEl?.dataset.groupId || null;
const next = mountEl?.dataset.next || "/groups/";

// The container renders its own <main-layout> (page header + gutter), so it is
// mounted directly here instead of being wrapped again.
entry(GroupEditContainer, { groupId, next }).mount("#group-edit");
