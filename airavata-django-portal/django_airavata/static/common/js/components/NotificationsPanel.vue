<template>
  <div class="notifications-panel">
    <div class="sidebar-header">
      <h6 class="sidebar-header__title">Notifications</h6>
    </div>
    <div v-if="notices.length === 0" class="text-center text-muted p-3" style="font-size:0.8125rem;">
      No notifications
    </div>
    <div
      v-for="notice in notices"
      :key="notice.notificationId"
      class="notification-item"
      :class="{ 'notification-item--unread': !notice.is_read }"
    >
      <div class="d-flex justify-content-between align-items-start">
        <span class="notification-item__title" :class="textColor(notice)">{{ notice.title }}</span>
        <a
          v-if="!notice.is_read"
          href="#"
          class="notification-item__action"
          title="Mark as read"
          @click.prevent="markRead(notice)"
        ><i class="fas fa-check-circle"></i></a>
      </div>
      <div class="notification-item__body">{{ notice.notificationMessage }}</div>
      <div class="notification-item__time">{{ fromNow(notice.publishedTime) }}</div>
    </div>
  </div>
</template>

<script>
import { utils } from "django-airavata-api";

export default {
  name: "notifications-panel",
  props: {
    notices: { type: Array, default: () => [] },
    unreadCount: { type: Number, default: 0 },
  },
  emits: ["update:unread"],
  methods: {
    markRead(notice) {
      utils.FetchUtils.get(notice.url).then(() => {
        notice.is_read = true;
        this.$emit("update:unread", this.unreadCount - 1);
      });
    },
    fromNow(date) {
      const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
      const diffMs = new Date(date) - Date.now();
      const diffSecs = Math.round(diffMs / 1000);
      const diffMins = Math.round(diffSecs / 60);
      const diffHours = Math.round(diffMins / 60);
      const diffDays = Math.round(diffHours / 24);
      if (Math.abs(diffSecs) < 60) return rtf.format(diffSecs, "second");
      if (Math.abs(diffMins) < 60) return rtf.format(diffMins, "minute");
      if (Math.abs(diffHours) < 24) return rtf.format(diffHours, "hour");
      return rtf.format(diffDays, "day");
    },
    textColor(notice) {
      if (notice.priority === 0) return "text-primary";
      if (notice.priority === 1) return "text-warning";
      if (notice.priority === 2) return "text-danger";
      return "";
    },
  },
};
</script>
