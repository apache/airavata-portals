<template>
  <div class="flex flex-1 flex-row overflow-y-auto">
    <main class="flex-1" :class="hasSidebar ? 'overflow-y-auto p-4' : 'p-4'">
      <notifications-display />
      <div class="w-full">
        <slot />
      </div>
    </main>
    <slot name="sidebar" />
  </div>
</template>

<script>
import NotificationsDisplay from "./NotificationsDisplay.vue";

export default {
  name: "main-layout",
  computed: {
    hasSidebar() {
      return Boolean(this.$slots.sidebar);
    },
  },
  components: {
    NotificationsDisplay,
  },
};
</script>
