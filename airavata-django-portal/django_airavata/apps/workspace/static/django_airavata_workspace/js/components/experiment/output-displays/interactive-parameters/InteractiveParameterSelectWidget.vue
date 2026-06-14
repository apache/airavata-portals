<template>
  <select
    :value="value"
    class="border-input dark:bg-input/30 focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
    @change="$emit('input', $event.target.value)"
  >
    <option
      v-for="option in normalizedOptions"
      :key="option.value"
      :value="option.value"
    >
      {{ option.text }}
    </option>
  </select>
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
    normalizedOptions() {
      return (this.parameter.options || []).map((option) =>
        option !== null && typeof option === "object"
          ? { value: option.value, text: option.text ?? option.value }
          : { value: option, text: option }
      );
    },
  },
};
</script>
