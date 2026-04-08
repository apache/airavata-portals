import { createApp, h } from "vue";
import GatewayNoticesContainer from "./components/GatewayNoticesContainer";

const el = document.getElementById("gateway-notices");
if (el) {
  const app = createApp({
    data() {
      return {
        unreadCount: null,
        notices: null,
      };
    },
    beforeMount() {
      this.unreadCount = parseInt(this.$el.dataset.unreadCount);
      this.notices = JSON.parse(this.$el.dataset.notices);
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
