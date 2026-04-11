import { createApp, h } from "vue";
import GatewayNoticesContainer from "./components/GatewayNoticesContainer.vue";

const el = document.getElementById("gateway-notices");
if (el) {
  const unreadCount = parseInt(el.dataset.unreadCount || "0");
  const notices = JSON.parse(el.dataset.notices || "[]");
  const app = createApp({
    data() {
      return { unreadCount, notices };
    },
    render() {
      return h(GatewayNoticesContainer, {
        unreadCount: this.unreadCount,
        notices: this.notices,
      });
    },
  });
  app.mount("#gateway-notices");
}
