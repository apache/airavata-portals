<template>
  <div class="flex flex-1 flex-row overflow-y-auto">
    <main class="flex-1 overflow-y-auto">
      <!-- Consistent page gutter so content is never edge-to-edge. -->
      <div class="mx-auto w-full max-w-screen-2xl px-6 py-6 lg:px-8">
        <notifications-display class="mb-4 empty:mb-0" />
        <!-- Standard page header: title + optional subtitle + actions. -->
        <header
          v-if="title || subtitle || $slots.title || $slots.actions"
          class="mb-6 flex flex-wrap items-start justify-between gap-x-4 gap-y-2"
        >
          <div class="min-w-0">
            <slot name="title">
              <h1 class="text-2xl font-semibold tracking-tight text-foreground">
                {{ title }}
              </h1>
            </slot>
            <slot name="subtitle">
              <p v-if="subtitle" class="mt-1 text-sm text-muted-foreground">
                {{ subtitle }}
              </p>
            </slot>
          </div>
          <div
            v-if="$slots.actions"
            class="flex shrink-0 flex-wrap items-center gap-2"
          >
            <slot name="actions" />
          </div>
        </header>
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
  props: {
    // Per-page title + subtitle so every page has a consistent header. Pages can
    // also override via the #title / #subtitle / #actions slots.
    title: { type: String, default: "" },
    subtitle: { type: String, default: "" },
  },
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
