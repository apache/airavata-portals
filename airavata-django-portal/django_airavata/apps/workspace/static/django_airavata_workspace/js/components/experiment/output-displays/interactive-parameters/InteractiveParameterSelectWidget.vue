<template>
  <select class="form-select" :value="value" @change="$emit('input', $event.target.value)">
    <option v-for="opt in options" :key="opt.value" :value="opt.value">
      {{ opt.text }}
    </option>
  </select>
</template>

<script>
export default {
  name: "InteractiveParameterSelectWidget",
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
