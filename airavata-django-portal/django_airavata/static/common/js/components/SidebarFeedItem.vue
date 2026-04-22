<template>
  <li class="feed__list-item">
    <span v-if="feedItem.type" class="feed__label text-secondary">{{ feedItem.type }}</span>
    <h2 class="feed__title mb-2">
      <a v-if="feedItem.url" :href="feedItem.url">{{ feedItem.title }}</a>
      <span v-else>{{ feedItem.title }}</span>
    </h2>
    <slot :feed-item="feedItem">
      <div v-if="feedItem.description">{{ feedItem.description }}</div>
    </slot>
    <div v-if="timestamp" class="feed__item-meta text-secondary mt-1">
      <span>Updated </span> <time>{{ timestamp }}</time>
    </div>
  </li>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { relativeTime } from "../utils/dates";

interface FeedItem {
  type?: string;
  url?: string;
  title: string;
  timestamp?: string | number | Date;
  description?: string;
  id?: string | number;
}

const props = defineProps<{
  feedItem: FeedItem;
}>();

const timestamp = computed(() => {
  if (props.feedItem.timestamp) {
    return relativeTime(props.feedItem.timestamp);
  } else {
    return null;
  }
});
</script>
