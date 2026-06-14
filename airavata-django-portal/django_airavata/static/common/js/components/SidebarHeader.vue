<template>
  <header class="flex items-center border-b border-border p-6">
    <h1 class="m-0 text-sm font-medium uppercase tracking-wide">{{ title }}</h1>
    <a
      :href="viewAllUrl"
      class="ml-auto text-sm text-primary hover:underline"
      >View all</a
    >
  </header>
</template>

<script>
export default {
  name: "sidebar-header",
  props: {
    title: {
      type: String,
      default: "Recent Activity",
    },
    viewAllUrl: {
      type: String,
    },
  },
};
</script>
