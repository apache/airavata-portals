<template>
  <button class="app-footer__toggle" title="Notifications" @click="showNotifications">
    <i class="fa fa-bell"></i>
    <span v-if="localUnreadCount > 0" class="app-footer__badge">{{ localUnreadCount }}</span>
  </button>
</template>

<script>
export default {
  name: "GatewayNoticesContainer",
  props: ["notices", "unreadCount"],
  data() {
    return {
      localUnreadCount: this.unreadCount,
    };
  },
  methods: {
    showNotifications() {
      window.dispatchEvent(new CustomEvent("sidebar:show", { detail: "notifications" }));
    },
  },
};
</script>
