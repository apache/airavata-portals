<template>
  <select
    :id="id"
    v-model="data"
    :disabled="readOnly"
    :aria-invalid="componentValidState === false"
    class="border-input dark:bg-input/30 focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 aria-invalid:border-destructive h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
    @change="valueChanged"
  >
    <option
      v-for="option in selectOptions"
      :key="option.value"
      :value="option.value"
    >
      {{ option.text }}
    </option>
  </select>
</template>

<script>
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";

const CONFIG_OPTION_TEXT_KEY = "text";
const CONFIG_OPTION_VALUE_KEY = "value";

export default {
  name: "select-input-editor",
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
