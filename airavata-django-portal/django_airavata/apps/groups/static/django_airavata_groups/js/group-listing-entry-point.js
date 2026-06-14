import { entry } from "django-airavata-common-ui";
import GroupsManageContainer from "./containers/GroupsManageContainer.vue";

// Tailwind v4 + shadcn-vue design tokens and base styles.
import "django-airavata-common-ui/css/app.css";

// The container renders its own <main-layout> (page header + gutter), so it is
// mounted directly here instead of being wrapped again.
entry(GroupsManageContainer).mount("#group-list");
