<template>
  <VueSlider
    v-model="sliderValues"
    :state="componentValidState"
    :disabled="readOnly"
    :min="sliderMin"
    :max="sliderMax"
    :interval="sliderStep"
    tooltip="always"
    :tooltip-formatter="tooltipFormatter"
    :enable-cross="false"
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
    delimiter?: string;
  }>(),
  { modelValue: null, experiment: undefined, readOnly: false, min: undefined, max: undefined, step: undefined, valueFormat: undefined, displayFormat: undefined, delimiter: undefined },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
}>();

const { data, editorConfig, componentValidState, valueChanged } = useInputEditor(
  props,
  (_, v) => emit("update:modelValue", v),
  () => emit("valid"),
  (msgs) => emit("invalid", msgs),
);

const sliderValues = ref<number[]>([0, 100]);

const sliderMin = computed<number>(() =>
  typeof props.min !== "undefined"
    ? props.min
    : "min" in editorConfig.value
      ? (editorConfig.value.min as number)
      : 0,
);

const sliderMax = computed<number>(() =>
  typeof props.max !== "undefined"
    ? props.max
    : "max" in editorConfig.value
      ? (editorConfig.value.max as number)
      : 100,
);

const sliderStep = computed<number>(() =>
  typeof props.step !== "undefined"
    ? props.step
    : "step" in editorConfig.value
      ? (editorConfig.value.step as number)
      : 1,
);

const sliderDelimiter = computed<string>(() =>
  props.delimiter
    ? props.delimiter
    : "delimiter" in editorConfig.value
      ? (editorConfig.value.delimiter as string)
      : "-",
);

watch(data, () => {
  initializeSliderValues();
});

onMounted(() => {
  initializeSliderValues();
});

function initializeSliderValues() {
  sliderValues.value = parseValue(data.value);
  if (data.value !== formatValue(sliderValues.value)) {
    onChange(sliderValues.value);
  }
}

function parseValue(value: string | null): number[] {
  const result = value
    ? value.replaceAll("%", "").split(sliderDelimiter.value).map(parseFloat)
    : [];
  return result.length === 2 && !isNaN(result[0]) && !isNaN(result[1])
    ? result
    : [sliderMin.value, sliderMax.value];
}

function onChange(value: number[]) {
  data.value = formatValue(value);
  valueChanged();
}

function tooltipFormatter(value: number): string {
  if (props.displayFormat) {
    if (props.displayFormat === "percentage") {
      return `${value}%`;
    }
  } else if ("displayFormat" in editorConfig.value) {
    if ((editorConfig.value.displayFormat as Record<string, unknown>)?.percentage) {
      return `${value}%`;
    }
  }
  return String(value);
}

function formatValue(value: number[]): string {
  let values = value.map(String);
  if (props.valueFormat) {
    if (props.valueFormat === "percentage") {
      values = values.map((v) => `${v}%`);
    }
  } else if ("valueFormat" in editorConfig.value) {
    if ((editorConfig.value.valueFormat as Record<string, unknown>)?.percentage) {
      values = values.map((v) => `${v}%`);
    }
  }
  return values.join(sliderDelimiter.value);
}
</script>
