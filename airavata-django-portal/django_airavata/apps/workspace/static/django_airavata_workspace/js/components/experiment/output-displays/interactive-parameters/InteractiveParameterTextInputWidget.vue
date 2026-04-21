<template>
  <div class="input-group">
    <input
      ref="textInput"
      class="form-control"
      :value="value"
      @input="currentValue = $event"
      @keydown.enter="enterKeyPressed"
    />
    <span class="input-group-text">
      <button class="btn btn-primary" :disabled="disabled" @click="submit">Submit</button>
    </span>
  </div>
</template>

<script>
export default {
  name: "InteractiveParameterTextInputWidget",
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
