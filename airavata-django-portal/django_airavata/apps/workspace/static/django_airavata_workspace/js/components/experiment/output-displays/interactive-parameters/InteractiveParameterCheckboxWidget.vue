<template>
  <div class="form-check"><input class="form-check-input" type="checkbox" :checked="value" @input="$emit('input', $event)" />
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
