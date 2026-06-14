<template>
  <div>
    <input
      ref="rangeInput"
      type="range"
      class="w-full accent-primary"
      :value="value"
      :min="parameter.min"
      :max="parameter.max"
      :step="parameter.step || 'any'"
      @input="updateValue($event.target.value)"
      @mouseup="mouseUp"
      @keyup="keyUp"
    />
    <small class="text-muted-foreground">Value: {{ roundedValue }}</small>
  </div>
</template>

<script>
export default {
  name: "interactive-parameter-range-widget",
  props: {
    value: {
      type: Number,
      required: true,
    },
    parameter: {
      type: Object,
    },
  },
  data() {
    return {
      currentValue: parseFloat(this.value),
    };
  },
  computed: {
    disabled() {
      return this.currentValue === this.initialValue;
    },
    initialValue() {
      return parseFloat(this.value);
    },
    roundedValue() {
      return this.currentValue ? this.currentValue.toFixed(2) : null;
    },
  },
  methods: {
    updateValue(newValue) {
      this.currentValue = parseFloat(newValue);
    },
    submit() {
      this.$emit("input", this.currentValue);
    },
    mouseUp() {
      this.$refs.rangeInput.blur();
      if (!this.disabled) {
        this.submit();
      }
    },
    keyUp() {},
  },
};
</script>
