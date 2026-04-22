<template>
  <button class="app-footer__toggle" title="Notifications" @click="showNotifications">
    <i class="fa fa-bell"></i>
    <span v-if="localUnreadCount > 0" class="app-footer__badge">{{ localUnreadCount }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  notices?: unknown[];
  unreadCount?: number;
}>();

const localUnreadCount = ref(props.unreadCount ?? 0);

function showNotifications(): void {
  window.dispatchEvent(new CustomEvent("sidebar:show", { detail: "notifications" }));
}
</script>
