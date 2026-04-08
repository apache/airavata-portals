
import { utils } from "django-airavata-common-ui";
import store from "../store";

export default {
  props: {
    modelValue: String,
    name: String,
  },
  emits: ["update:modelValue"],
  // TODO: web components need Vue 3 defineCustomElement migration
  // store: store,
  data() {
    return {
      data: this.modelValue,
    };
  },
  computed: {
    readOnly() {
      return this.experimentInput.isReadOnly;
    },
    id() {
      return utils.sanitizeHTMLId(this.experimentInput.name);
    },
    experimentInput() {
      return this.$store.getters.getExperimentInputByName(this.name);
    },
  },
  methods: {
    valueChanged(value) {
      if (value !== this.data) {
        this.data = value;
        this.$emit("update:modelValue", this.data);
        const inputEvent = new CustomEvent("input", {
          detail: [this.data],
          composed: true,
          bubbles: true,
        });
        this.$el.dispatchEvent(inputEvent);
      }
    },
  },
  watch: {
    modelValue(value) {
      this.data = value;
    },
  },
};
