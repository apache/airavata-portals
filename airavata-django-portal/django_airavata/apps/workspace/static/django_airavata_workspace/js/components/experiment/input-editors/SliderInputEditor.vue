<template>
  <vue-slider
    v-model="sliderValue"
    :state="componentValidState"
    :disabled="readOnly"
    :min="sliderMin"
    :max="sliderMax"
    :interval="sliderStep"
    tooltip="always"
    :tooltip-formatter="tooltipFormatter"
    @change="onChange"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models } from "django-airavata-api";
import { useInputEditor } from "@/composables/useInputEditor";
import VueSlider from "vue-slider-component";

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    experimentInput: InputDataObjectType;
    experiment?: Experiment;
    id: string;
    readOnly?: boolean;
    min?: number;
    max?: number;
    step?: number;
    valueFormat?: string;
    displayFormat?: string;
  }>(),
  { modelValue: null, experiment: undefined, readOnly: false, min: undefined, max: undefined, step: undefined, valueFormat: undefined, displayFormat: undefined },
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

const sliderValue = ref<number | undefined>(undefined);

const sliderMin = computed(() =>
  typeof props.min !== "undefined"
    ? props.min
    : "min" in editorConfig.value
      ? (editorConfig.value.min as number)
      : 0,
);
const sliderMax = computed(() =>
  typeof props.max !== "undefined"
    ? props.max
    : "max" in editorConfig.value
      ? (editorConfig.value.max as number)
      : 100,
);
const sliderStep = computed(() =>
  typeof props.step !== "undefined"
    ? props.step
    : "step" in editorConfig.value
      ? (editorConfig.value.step as number)
      : 1,
);

watch(data, () => { initializeSliderValue(); });

onMounted(() => { initializeSliderValue(); });

function parseValue(value: string | null): number {
  const result = value ? parseFloat(value.replaceAll("%", "")) : NaN;
  return !isNaN(result) ? result : sliderMin.value;
}

function tooltipFormatter(value: number): string {
  if (props.displayFormat) {
    if (props.displayFormat === "percentage") return `${value}%`;
  } else if ("displayFormat" in editorConfig.value) {
    if ((editorConfig.value.displayFormat as { percentage?: boolean }).percentage) return `${value}%`;
  }
  return String(value);
}

function formatValue(value: number): string {
  if (props.valueFormat) {
    if (props.valueFormat === "percentage") return `${value}%`;
  } else if ("valueFormat" in editorConfig.value) {
    if ((editorConfig.value.valueFormat as { percentage?: boolean }).percentage) return `${value}%`;
  }
  return String(value);
}

function onChange(value: number) {
  data.value = formatValue(value);
  valueChanged();
}

function initializeSliderValue() {
  sliderValue.value = parseValue(data.value);
  // If parsing the value resulted in it changing (failed to parse so
  // initialized to the 'sliderMin'), update the value
  if (data.value !== formatValue(sliderValue.value)) {
    onChange(sliderValue.value);
  }
}
</script>
