<template>
  <a :href="viewData.url">{{ viewData.label }}</a>
</template>

<script>
export default {
  name: "LinkOutputDisplay",
  props: {
    viewData: {
      type: Object,
      required: true,
    },
  },
};
</script>
