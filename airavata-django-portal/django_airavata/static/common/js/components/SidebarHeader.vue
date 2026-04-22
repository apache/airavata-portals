<template>
  <header class="sidebar-header">
    <h1 class="sidebar-header__title">{{ title }}</h1>
    <a :href="viewAllUrl" class="sidebar-header__action">View all</a>
  </header>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  title?: string;
  viewAllUrl?: string;
}>(), {
  title: "Recent Activity",
  viewAllUrl: undefined,
});
</script>
