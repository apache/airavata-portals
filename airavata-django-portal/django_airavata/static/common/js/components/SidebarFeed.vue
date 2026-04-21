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

<script>
import SidebarFeedItem from "./SidebarFeedItem.vue";

export default {
  name: "SidebarFeed",
  components: {
    SidebarFeedItem,
  },
  props: {
    feedItems: {
      type: Array,
      default: function () {
        return [];
      },
    },
  },
};
</script>
