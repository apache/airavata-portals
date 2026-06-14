<template>
  <select
    :value="value"
    :class="nativeSelectClass"
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
import { NATIVE_SELECT_CLASS } from "../../../../lib/utils";

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
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>.
      return NATIVE_SELECT_CLASS;
    },
    options() {
      return this.parameter.options;
    },
    normalizedOptions() {
      return (this.parameter.options || []).map((option) =>
        option !== null && typeof option === "object"
          ? { value: option.value, text: option.text ?? option.value }
          : { value: option, text: option },
      );
    },
  },
};
</script>
