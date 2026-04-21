// InputEditorMixin: mixin for experiment InputEditors, provides basic v-model
// and validation functionality and defines the basic props interface
// (experimentInput and id).
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
      // TODO: asyncComputed removed in Vue 3 - these need to be converted to
      // watch + async methods or composables
      validationResults: { value: [] },
      validationMessages: [],
      valid: false,
      componentValidState: null,
    };
  },
  computed: {
    editorConfig: function () {
      return this.experimentInput.editorConfig;
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
    async updateValidation() {
      const results = this.experimentInput.validate(this.data);
      let value = [];
      if ("value" in results) {
        value = await Promise.all(results["value"]).then((arr) => arr.filter((x) => x !== null));
      }
      this.validationResults = { value };
      this.validationMessages = value;
      this.valid = this.validationMessages.length === 0;
      this.componentValidState = this.inputHasBegun ? this.valid : null;
      this.checkValidation();
    },
  },
  created: function () {
    this.updateValidation();
  },
  watch: {
    modelValue(newValue) {
      this.data = newValue;
    },
    data() {
      this.updateValidation();
    },
  },
};
