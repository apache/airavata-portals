import { utils } from "django-airavata-common-ui";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

export default {
  props: {
    modelValue: String,
    name: String,
  },
  emits: ["update:modelValue"],
  setup() {
    const webComponentsStore = useWebComponentsStore();
    return { webComponentsStore };
  },
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
      return this.webComponentsStore.getExperimentInputByName(this.name);
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
