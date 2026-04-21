<template>
  <nav v-if="crumbs.length > 0" aria-label="breadcrumb" class="mb-3">
    <ol class="breadcrumb mb-0">
      <li
        v-for="(crumb, index) in crumbs"
        :key="index"
        class="breadcrumb-item"
        :class="{ active: index === crumbs.length - 1 }"
      >
        <a v-if="index < crumbs.length - 1" :href="crumb.url">{{ crumb.label }}</a>
        <span v-else>{{ crumb.label }}</span>
      </li>
    </ol>
  </nav>
</template>

<script>
export default {
  name: "BreadcrumbNav",
  props: {
    crumbs: {
      type: Array,
      required: true,
    },
  },
};
</script>
