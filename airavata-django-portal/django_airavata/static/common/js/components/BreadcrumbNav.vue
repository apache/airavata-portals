<template>
  <nav aria-label="breadcrumb" class="mb-3" v-if="crumbs.length > 0">
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
  name: "breadcrumb-nav",
  props: {
    crumbs: {
      type: Array,
      required: true,
    },
  },
};
</script>
