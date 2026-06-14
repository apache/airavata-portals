import { models } from "django-airavata-api";

export default {
  watch: {
    data: {
      handler: function (newValue, oldValue) {
        // Only emit for objects when one of their deep properties has changed to
        // prevent an infinite loop, since 'data' is recloned whenever the model
        // value changes.
        if (typeof this.modelValue === "object" && newValue === oldValue) {
          this.$emit("update:modelValue", newValue);
        } else if (
          (this.modelValue === null || typeof this.modelValue !== "object") &&
          newValue !== oldValue
        ) {
          this.$emit("update:modelValue", newValue);
        }
      },
      deep: true,
    },
    modelValue: {
      handler: function (newValue) {
        this.data = this.copyValue(newValue);
      },
      deep: true,
    },
  },
  methods: {
    copyValue(value) {
      if (value instanceof Array) {
        return value.map((item) => this.copyValue(item));
      } else {
        if (value === null) {
          return null;
        } else if (value instanceof models.BaseModel) {
          return value.clone();
        } else if (typeof value === "object") {
          return JSON.parse(JSON.stringify(value));
        } else {
          // Must be number, boolean or string
          return value;
        }
      }
    },
  },
  data: function () {
    return {
      data: this.copyValue(this.modelValue),
    };
  },
  props: {
    modelValue: {
      required: true,
    },
  },
};
