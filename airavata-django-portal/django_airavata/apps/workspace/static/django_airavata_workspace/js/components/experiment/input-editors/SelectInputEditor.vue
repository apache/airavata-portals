<template>
  <select
    :id="id"
    v-model="data"
    class="form-select"
    :disabled="readOnly"
    :state="componentValidState"
    @change="valueChanged"
  >
    <option :value="null" disabled>Select...</option>
    <option v-for="opt in selectOptions" :key="opt.value" :value="opt.value">
      {{ opt.text }}
    </option>
  </select>
</template>

<script>
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";

const CONFIG_OPTION_TEXT_KEY = "text";
const CONFIG_OPTION_VALUE_KEY = "value";

export default {
  name: "SelectInputEditor",
  mixins: [InputEditorMixin],
  props: {
    value: {
      type: String,
    },
    options: {
      type: Array,
    },
  },
  computed: {
    selectOptions: function () {
      const options = this.options || this.editorConfig.options || [];
      return options.map((option) => {
        return {
          text: option[CONFIG_OPTION_TEXT_KEY],
          value: option[CONFIG_OPTION_VALUE_KEY],
        };
      });
    },
  },
};
</script>
