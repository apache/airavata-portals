import GatewayNoticesContainer from "./components/GatewayNoticesContainer";
import entry from "./entry";

// Read the server-rendered data attributes off the mount element before Vue 3
// replaces its contents, then start the app with them as root props.
const el = document.querySelector("#gateway-notices");
const unreadCount = el ? parseInt(el.dataset.unreadCount) : null;
const notices = el ? JSON.parse(el.dataset.notices) : null;

entry(GatewayNoticesContainer, { unreadCount, notices }).mount("#gateway-notices");
