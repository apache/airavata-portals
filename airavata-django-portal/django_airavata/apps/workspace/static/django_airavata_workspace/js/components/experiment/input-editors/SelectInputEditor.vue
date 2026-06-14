<template>
  <select
    :id="id"
    v-model="data"
    :disabled="readOnly"
    :aria-invalid="componentValidState === false"
    :class="nativeSelectClass"
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
import { NATIVE_SELECT_CLASS } from "../../../lib/utils";

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
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>, plus the
      // invalid-state ring so it mirrors `:aria-invalid` on shadcn controls.
      return `${NATIVE_SELECT_CLASS} aria-invalid:border-destructive aria-invalid:ring-destructive/40`;
    },
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
