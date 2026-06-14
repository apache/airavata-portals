<template>
  <Checkbox
    :model-value="value"
    @update:model-value="$emit('input', $event)"
  />
</template>

<script>
export default {
  name: "interactive-parameter-checkbox-widget",
  props: {
    value: {
      type: Boolean,
      required: true,
    },
  },
};
</script>
