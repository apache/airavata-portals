// InputEditorMixin: mixin for experiment InputEditors, provides basic v-model
// and validation functionality and defines the basic props interface
// (experimentInput and id).
//
// Vue 3 notes:
// - The v-model contract is the Vue 3 default: `modelValue` prop +
//   `update:modelValue` event (was `value`/`input` under Vue 2).
// - Validation is asynchronous (InputDataObjectType.validate may return
//   Promises). Vue 2 used vue-async-computed for this; Vue 3 has no equivalent,
//   so the async results are kept in reactive data (`validationMessages`,
//   `valid`) and recomputed via `runValidation()` whenever the value changes.
import { models } from "django-airavata-api";
export default {
  props: {
    modelValue: {
      type: String,
    },
    experimentInput: {
      type: models.InputDataObjectType,
      required: true,
    },
    experiment: {
      type: models.Experiment,
      required: false,
    },
    id: {
      type: String,
      required: true,
    },
    readOnly: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["update:modelValue", "valid", "invalid"],
  data() {
    return {
      data: this.modelValue,
      inputHasBegun: false,
      // Mirrors the vue-async-computed defaults: no messages, so `valid` starts
      // true until the first asynchronous validation pass completes.
      validationMessages: [],
      valid: true,
    };
  },
  computed: {
    editorConfig: function () {
      return this.experimentInput.editorConfig;
    },
    componentValidState: function () {
      if (this.inputHasBegun) {
        return this.valid;
      } else {
        return null;
      }
    },
  },
  methods: {
    valueChanged: function () {
      this.inputHasBegun = true;
      this.$emit("update:modelValue", this.data);
    },
    checkValidation: function () {
      if (this.valid) {
        this.$emit("valid");
      } else {
        this.$emit("invalid", this.validationMessages);
      }
    },
    runValidation: async function () {
      const results = this.experimentInput.validate(this.data);
      let messages = [];
      if ("value" in results) {
        const resolved = await Promise.all(results["value"]);
        messages = resolved.filter((x) => x !== null);
      }
      this.validationMessages = messages;
      this.valid = messages.length === 0;
      this.checkValidation();
    },
  },
  created: function () {
    this.runValidation();
  },
  watch: {
    modelValue(newValue) {
      this.data = newValue;
    },
    data() {
      this.runValidation();
    },
  },
};
