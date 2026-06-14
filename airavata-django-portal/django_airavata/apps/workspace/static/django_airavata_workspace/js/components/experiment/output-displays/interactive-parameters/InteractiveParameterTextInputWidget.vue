<template>
  <div class="flex">
    <input
      ref="textInput"
      :value="value"
      class="border-input dark:bg-input/30 focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full min-w-0 rounded-l-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-3"
      @input="currentValue = $event.target.value"
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
