<template>
  <b-input-group>
    <b-form-input
      ref="textInput"
      :model-value="value"
      @update:model-value="currentValue = $event"
      @keydown.enter="enterKeyPressed"
    />
    <b-button variant="primary" :disabled="disabled" @click="submit"
      >Submit</b-button
    >
  </b-input-group>
</template>

<script>
export default {
  name: "interactive-parameter-text-input-widget",
  props: {
    value: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      currentValue: this.value,
    };
  },
  computed: {
    disabled() {
      return this.currentValue === this.value;
    },
  },
  methods: {
    submit() {
      this.$emit("input", this.currentValue);
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
