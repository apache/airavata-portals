<template>
  <li class="border-b border-border p-6">
    <span
      v-if="feedItem.type"
      class="text-xs uppercase text-muted-foreground"
      >{{ feedItem.type }}</span
    >
    <h2 class="mb-2 text-base font-normal">
      <a
        v-if="feedItem.url"
        :href="feedItem.url"
        class="text-foreground hover:underline"
        >{{ feedItem.title }}</a
      >
      <span v-else>{{ feedItem.title }}</span>
    </h2>
    <slot v-bind:feedItem="feedItem">
      <div v-if="feedItem.description">{{ feedItem.description }}</div>
    </slot>
    <div v-if="timestamp" class="mt-1 text-xs text-muted-foreground">
      <span>Updated </span> <time>{{ timestamp }}</time>
    </div>
  </li>
</template>

<script>
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

export default {
  name: "sidebar-feed-item",
  props: {
    /**
     * feedItem properties are
     * - type (String, Optional) the type of feed item (e.g. for Experiments this is the application name)
     * - url (String, Optional) url to link to the full item details
     * - title (String, Required) title of the feed item
     * - timestamp (Date, Optional) timestamp of when feed item was created/updated
     * - description (String, Optional) description of feed item. Displayed when no slot is provided.
     */
    feedItem: Object,
  },
  computed: {
    timestamp() {
      if (this.feedItem.timestamp) {
        return dayjs(this.feedItem.timestamp).fromNow();
      } else {
        return null;
      }
    },
  },
};
</script>
