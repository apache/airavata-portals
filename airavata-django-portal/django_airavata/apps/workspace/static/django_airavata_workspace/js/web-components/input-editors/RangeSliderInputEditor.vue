<template>
  <range-slider-input-editor
    v-if="experimentInput"
    :id="id"
    :value="data"
    :experiment-input="experimentInput"
    :read-only="readOnly"
    :min="min"
    :max="max"
    :step="step"
    :value-format="valueFormat"
    :display-format="displayFormat"
    :delimiter="delimiter"
    @input="valueChanged"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, getCurrentInstance } from "vue";
import RangeSliderInputEditor from "../../components/experiment/input-editors/RangeSliderInputEditor.vue";
import { utils } from "django-airavata-common-ui";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

interface ExperimentInput {
  isReadOnly: boolean;
  name: string;
}

const props = withDefaults(defineProps<{
  modelValue?: string;
  name?: string;
  min?: number;
  max?: number;
  step?: number;
  valueFormat?: string;
  displayFormat?: string;
  delimiter?: string;
}>(), {
  modelValue: undefined,
  name: undefined,
  min: undefined,
  max: undefined,
  step: undefined,
  valueFormat: undefined,
  displayFormat: undefined,
  delimiter: undefined,
});

const emit = defineEmits<{
  "update:modelValue": [value: string | undefined];
}>();

const webComponentsStore = useWebComponentsStore();

const data = ref<string | undefined>(props.modelValue);

const experimentInput = computed(() =>
  webComponentsStore.getExperimentInputByName(props.name ?? "") as unknown as ExperimentInput | null
);
const readOnly = computed(() => experimentInput.value?.isReadOnly ?? false);
const id = computed(() => utils.sanitizeHTMLId(experimentInput.value?.name ?? ""));

function valueChanged(value: string | undefined) {
  if (value !== data.value) {
    data.value = value;
    emit("update:modelValue", data.value);
    const instance = getCurrentInstance();
    const el = instance?.proxy?.$el as Element | undefined;
    if (el) {
      const inputEvent = new CustomEvent("input", {
        detail: [data.value],
        composed: true,
        bubbles: true,
      });
      el.dispatchEvent(inputEvent);
    }
  }
}

watch(() => props.modelValue, (value) => {
  data.value = value;
});
</script>

<style lang="scss">
@import "../styles";
// Need to explicitly import VueSlider's CSS because importing component scss doesn't work
// https://github.com/vuejs/vue-web-component-wrapper/issues/12
@import "~vue-slider-component/dist-css/vue-slider-component.css";
:host {
  display: block;
}
</style>
