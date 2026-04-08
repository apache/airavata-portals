<template>
  <div class="input-group">
    <input class="form-control"
      ref="textInput"
      :value="value"
      @input="currentValue = $event"
      @keydown.enter="enterKeyPressed"
    />
    <span class="input-group-text">
      <button class="btn" variant="primary" :disabled="disabled" @click="submit"
        >Submit</b-button
      >
    </span>
  </div>
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
