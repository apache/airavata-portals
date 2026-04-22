<template>
  <!-- NOTE: experimentInput is late bound, don't create component until it is available -->
  <!-- Important that input editor is wrapped in div. Input editor stops
  propagation on native input events, but we need for this component's input
  events to propagate. So the input editor should not be the root component. -->
  <div>
    <string-input-editor
      v-if="experimentInput"
      :id="id"
      :value="data"
      :experiment-input="experimentInput"
      :read-only="readOnly"
      @input="valueChanged"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, getCurrentInstance } from "vue";
import StringInputEditor from "../../components/experiment/input-editors/StringInputEditor.vue";
import { utils } from "django-airavata-common-ui";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

interface ExperimentInput {
  isReadOnly: boolean;
  name: string;
}

const props = withDefaults(defineProps<{
  modelValue?: string;
  name?: string;
}>(), {
  modelValue: undefined,
  name: undefined,
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
:host {
  display: block;
}
</style>
