<template>
  <ol v-if="feedItems && feedItems.length > 0" class="feed">
    <sidebar-feed-item v-for="feedItem in feedItems" :key="feedItem.id" :feed-item="feedItem">
      <template #default="slotProps">
        <div>
          <slot name="description" :feed-item="slotProps.feedItem" />
        </div>
      </template>
    </sidebar-feed-item>
  </ol>
</template>

<script setup lang="ts">
import SidebarFeedItem from "./SidebarFeedItem.vue";

interface FeedItem {
  id?: string | number;
  type?: string;
  url?: string;
  title: string;
  timestamp?: string | number | Date;
  description?: string;
}

withDefaults(defineProps<{
  feedItems?: FeedItem[];
}>(), {
  feedItems: () => [],
});
</script>
