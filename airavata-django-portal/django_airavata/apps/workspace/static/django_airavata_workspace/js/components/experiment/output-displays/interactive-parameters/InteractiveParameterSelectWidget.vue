<template>
  <b-form-select
    :model-value="value"
    :options="options"
    @update:model-value="$emit('input', $event)"
  />
</template>

<script>
export default {
  name: "interactive-parameter-select-widget",
  props: {
    value: {
      type: String,
      required: true,
    },
    parameter: {
      type: Object,
      required: true,
    },
  },
  computed: {
    options() {
      return this.parameter.options;
    },
  },
};
</script>
