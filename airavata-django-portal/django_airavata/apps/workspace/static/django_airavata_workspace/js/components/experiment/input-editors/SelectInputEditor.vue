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

<script setup lang="ts">
import { computed } from "vue";
import { models } from "django-airavata-api";
import { useInputEditor } from "@/composables/useInputEditor";

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;

interface ConfigOption {
  text: string;
  value: string;
  [key: string]: unknown;
}

const CONFIG_OPTION_TEXT_KEY = "text";
const CONFIG_OPTION_VALUE_KEY = "value";

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    experimentInput: InputDataObjectType;
    experiment?: Experiment;
    id: string;
    readOnly?: boolean;
    options?: ConfigOption[];
  }>(),
  { modelValue: null, experiment: undefined, options: undefined, readOnly: false },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
}>();

const { data, componentValidState, editorConfig, valueChanged } = useInputEditor(
  props,
  (_, v) => emit("update:modelValue", v),
  () => emit("valid"),
  (msgs) => emit("invalid", msgs),
);

const selectOptions = computed(() => {
  const options: ConfigOption[] = props.options || editorConfig.value.options || [];
  return options.map((option) => ({
    text: option[CONFIG_OPTION_TEXT_KEY] as string,
    value: option[CONFIG_OPTION_VALUE_KEY] as string,
  }));
});
</script>
