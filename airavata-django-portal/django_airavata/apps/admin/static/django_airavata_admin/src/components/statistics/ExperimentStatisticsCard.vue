<template>
  <div class="card statistics-card">
    <div class="text-right">
      <div class="statistic-count text-nowrap">
        <abbr :title="String(count)">{{ displayedCount }}</abbr>
      </div>
      <div>{{ title }}</div>
    </div>
    <a :class="'text-decoration-none text-' + linkVariant" @click="$emit('click')">
      <slot name="link-text">
        <div v-for="state in states" :key="state.value as PropertyKey">{{ state.name }}</div>
      </slot>
    </a>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    bgVariant?: string;
    headerTextVariant?: string;
    linkVariant?: string;
    count: number;
    title: string;
    states?: { value: unknown; name: string }[];
  }>(),
  {
    bgVariant: "light",
    headerTextVariant: "dark",
    linkVariant: "primary",
    states: () => [],
  }
);

defineEmits<{
  click: [];
}>();

const displayedCount = computed(() => {
  // Round large numbers and display m for 10^6 and k for 10^3
  if (props.count >= Math.pow(10, 6)) {
    return (props.count / Math.pow(10, 6)).toFixed(0) + "m";
  } else if (props.count >= Math.pow(10, 3)) {
    return (props.count / Math.pow(10, 3)).toFixed(0) + "k";
  } else {
    return props.count;
  }
});
</script>

<style scoped>
.statistic-count {
  font-size: 2.8rem;
  overflow: hidden;
}
.statistics-card {
  height: calc(100% - 30px);
}
abbr {
  text-decoration: none;
}
</style>
