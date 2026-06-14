<template>
  <div class="flex">
    <input
      ref="textInput"
      type="number"
      :value="value"
      :min="parameter.min"
      :max="parameter.max"
      :step="parameter.step || 'any'"
      class="border-input dark:bg-input/30 focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full min-w-0 rounded-l-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-3"
      @input="updateValue($event.target.value)"
      @keydown.enter="enterKeyPressed"
    />
    <Button
      variant="default"
      class="rounded-l-none"
      :disabled="disabled"
      @click="submit"
      >Submit</Button
    >
  </div>
</template>

<script>
export default {
  name: "interactive-parameter-stepper-widget",
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
      valid: false,
    };
  },
  computed: {
    disabled() {
      return !this.valid || this.currentValue === parseFloat(this.value);
    },
  },
  methods: {
    updateValue(newValue) {
      if ("max" in this.parameter) {
        newValue = Math.min(this.parameter.max, newValue);
      }
      if ("min" in this.parameter) {
        newValue = Math.max(this.parameter.min, newValue);
      }
      this.currentValue = parseFloat(newValue);
      if (this.$refs.textInput.validity.valid) {
        this.valid = true;
        this.$emit("valid");
      } else {
        this.valid = false;
        this.$emit("invalid", this.$refs.textInput.validationMessage);
      }
    },
    submit() {
      if (!this.disabled) {
        this.$emit("input", this.currentValue);
      }
    },
    enterKeyPressed() {
      if (!this.disabled) {
        this.$refs.textInput.blur();
        this.submit();
      }
    },
  },
};
</script>
