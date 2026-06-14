<template>
  <Tooltip>
    <TooltipTrigger as-child>
      <a
        href="#"
        class="inline-flex cursor-pointer items-center text-primary"
        @click.stop.prevent="toggleFavorite"
      >
        <Star
          class="favorite-toggle size-4"
          :class="iconClasses"
          :fill="favorite ? 'currentColor' : 'none'"
        />
        <span class="sr-only">Toggle favorite</span>
      </a>
    </TooltipTrigger>
    <TooltipContent>{{ titleText }}</TooltipContent>
  </Tooltip>
</template>

<script>
import { Star } from "@lucide/vue";

export default {
  name: "favorite-toggle",
  components: { Star },
  props: {
    favorite: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    toggleFavorite() {
      if (this.favorite) {
        this.$emit("unfavorite");
      } else {
        this.$emit("favorite");
      }
    },
  },
  computed: {
    iconClasses() {
      return this.favorite ? "text-primary" : "text-muted-foreground";
    },
    titleText() {
      if (this.favorite) {
        return "Unmark as favorite";
      } else {
        return "Mark as favorite";
      }
    },
  },
};
</script>
