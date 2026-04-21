<template>
  <textarea
    :id="id"
    v-model="jsonString"
    class="form-control"
    :rows="rows"
    :disabled="disabled"
    :state="state"
    @input="valueChanged"
  />
</template>

<script>
export default {
  name: "JsonEditor",
  props: {
    value: {
      type: Object,
    },
    id: String,
    rows: Number,
    disabled: Boolean,
  },
  data() {
    return {
      jsonString: this.value ? this.formatJSON(this.value) : null,
      state: null,
    };
  },
  watch: {
    value(newValue) {
      this.jsonString = newValue ? this.formatJSON(newValue) : null;
    },
  },
  methods: {
    formatJSON(value) {
      return JSON.stringify(value, null, 4);
    },
    valueChanged(newValue) {
      try {
        if (newValue) {
          const parsedValue = JSON.parse(newValue);
          this.$emit("input", parsedValue);
        } else {
          this.$emit("input", null);
        }
        this.state = true;
      } catch (e) {
        this.state = false;
      }
    },
  },
};
</script>
