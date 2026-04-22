<template>
  <a v-b-tooltip class="text-primary" :title="titleText" @click.stop="toggleFavorite">
    <i class="fa fa-star favorite-toggle" :class="classes"
      ><span class="visually-hidden">Toggle favorite</span></i
    >
  </a>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{
  favorite?: boolean;
}>(), {
  favorite: false,
});

const emit = defineEmits<{
  unfavorite: [];
  favorite: [];
}>();

const classes = computed(() => (props.favorite ? [] : ["not-favorite"]));

const titleText = computed(() =>
  props.favorite ? "Unmark as favorite" : "Mark as favorite",
);

function toggleFavorite(): void {
  if (props.favorite) {
    emit("unfavorite");
  } else {
    emit("favorite");
  }
}
</script>

<style scoped>
.not-favorite {
  color: #999999;
}
.not-favorite:hover {
  color: inherit;
}
</style>
