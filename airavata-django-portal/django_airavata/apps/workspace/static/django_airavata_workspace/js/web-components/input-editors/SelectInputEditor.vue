<template>
  <div>
    <select-input-editor
      v-if="experimentInput"
      :id="id"
      :value="data"
      :experiment-input="experimentInput"
      :read-only="readOnly"
      :options="allOptions"
      @input="valueChanged"
    >
    </select-input-editor>
    <div ref="optionsSlot" class="options-slot"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, getCurrentInstance } from "vue";
import SelectInputEditor from "../../components/experiment/input-editors/SelectInputEditor.vue";
import { utils } from "django-airavata-common-ui";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

interface ConfigOption {
  text: string;
  value: string;
  [key: string]: unknown;
}

interface ExperimentInput {
  isReadOnly: boolean;
  name: string;
}

const props = withDefaults(defineProps<{
  modelValue?: string;
  name?: string;
  options?: ConfigOption[];
}>(), {
  modelValue: undefined,
  name: undefined,
  options: undefined,
});

const emit = defineEmits<{
  "update:modelValue": [value: string | undefined];
}>();

const webComponentsStore = useWebComponentsStore();

// From WebComponentInputEditorMixin
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

// From InlineOptionsMixin
const optionsSlot = ref<Element | null>(null);
const inlineOptions = ref<ConfigOption[]>([]);

const allOptions = computed<ConfigOption[] | undefined>(() => {
  const result: ConfigOption[] = props.options ? props.options.slice() : [];
  result.push(...inlineOptions.value);
  return result.length > 0 ? result : undefined;
});

function readInlineOptions() {
  const slotEl = optionsSlot.value?.querySelector("slot") as HTMLSlotElement | null;
  if (!slotEl) return;
  const els = slotEl.assignedElements();
  inlineOptions.value = [];
  for (const el of els) {
    if (el.tagName === "OPTION") {
      const opt = el as HTMLOptionElement;
      inlineOptions.value.push({ text: opt.textContent ?? "", value: opt.value });
    }
  }
}

function addInlineOptionsChangeListener() {
  const slotEl = optionsSlot.value?.querySelector("slot") as HTMLSlotElement | null;
  if (!slotEl) return;
  slotEl.addEventListener("slotchange", readInlineOptions);
}

function removeInlineOptionsChangeListener() {
  const slotEl = optionsSlot.value?.querySelector("slot") as HTMLSlotElement | null;
  if (!slotEl) return;
  slotEl.removeEventListener("slotchange", readInlineOptions);
}

onMounted(() => {
  if (optionsSlot.value) {
    optionsSlot.value.append(document.createElement("slot"));
    readInlineOptions();
    addInlineOptionsChangeListener();
  }
});

onUnmounted(() => {
  removeInlineOptionsChangeListener();
});
</script>

<style lang="scss">
@import "../styles";
:host {
  display: block;
}
:host .options-slot {
  display: none;
}
</style>
