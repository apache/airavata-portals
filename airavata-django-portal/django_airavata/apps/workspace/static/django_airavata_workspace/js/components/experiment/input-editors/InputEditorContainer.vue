<template>
  <InputEditorFormGroup
    :label="experimentInput.name"
    :label-for="inputEditorComponentId"
    :state="validationState"
    :feedback-messages="validationFeedback"
    :description="experimentInput.user_friendly_description"
  >
    <component
      :is="inputEditorComponentName"
      :id="inputEditorComponentId"
      v-model="data"
      :experiment-input="experimentInput"
      :experiment="experiment"
      :read-only="experimentInput.is_read_only"
      @invalid="recordInvalidInputEditorValue"
      @valid="recordValidInputEditorValue"
      @input="valueChanged"
      @uploadstart="uploadStart"
      @uploadend="uploadEnd"
    />
  </InputEditorFormGroup>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models } from "django-airavata-api";
import { utils } from "django-airavata-common-ui";
import FileInputEditor from "./FileInputEditor.vue";
import InputEditorFormGroup from "./InputEditorFormGroup.vue";
import MultiFileInputEditor from "./MultiFileInputEditor.vue";
import StringInputEditor from "./StringInputEditor.vue";

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;

const props = defineProps<{
  modelValue: string | null;
  experimentInput: InputDataObjectType;
  experiment: Experiment;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
  uploadstart: [];
  uploadend: [];
}>();

// VModelMixin inline: local data synced with modelValue
const data = ref<string | null>(props.modelValue);

watch(
  () => props.modelValue,
  (newVal) => {
    // Only update when the reference changes or primitive changes
    if (newVal !== data.value) {
      data.value = newVal;
    }
  },
);

watch(data, (newVal, oldVal) => {
  if (typeof props.modelValue === "object" && newVal === oldVal) {
    emit("update:modelValue", newVal);
  } else if ((props.modelValue === null || typeof props.modelValue !== "object") && newVal !== oldVal) {
    emit("update:modelValue", newVal);
  }
});

const state = ref<boolean | null>(null);
const feedbackMessages = ref<string[]>([]);
const inputHasBegun = ref(false);
const oldValue = ref<string | null>(null);
const show = ref(props.experimentInput.show);

// Map input type to component reference (string fallback for plugin-defined components)
const inputEditorComponentName = computed<unknown>(() => {
  if (props.experimentInput.editorUIComponentId) {
    // Plugin-defined component ID — must be globally registered by the plugin
    return props.experimentInput.editorUIComponentId as string;
  }
  if (props.experimentInput.type === models.DataType.URI) {
    return FileInputEditor;
  } else if (props.experimentInput.type === models.DataType.URI_COLLECTION) {
    return MultiFileInputEditor;
  }
  return StringInputEditor;
});

const inputEditorComponentId = computed<string>(() =>
  utils.sanitizeHTMLId(props.experimentInput.name),
);

const validationFeedback = computed(() => (inputHasBegun.value ? feedbackMessages.value : null));
const validationState = computed(() => (inputHasBegun.value ? state.value : null));

watch(
  () => props.experimentInput.show,
  (newValue) => {
    show.value = newValue;
  },
);

watch(show, (newValue, oldValue_) => {
  if (oldValue_ && !newValue) {
    handleHidingInput();
  } else if (newValue && !oldValue_) {
    handleShowingInput();
  }
});

onMounted(() => {
  if (!show.value) {
    handleHidingInput();
  }
});

function recordValidInputEditorValue() {
  state.value = true;
  emit("valid");
}

function recordInvalidInputEditorValue(messages: string[]) {
  feedbackMessages.value = messages;
  state.value = false;
  emit("invalid", messages);
}

function valueChanged() {
  inputHasBegun.value = true;
}

function handleHidingInput() {
  oldValue.value = data.value;
  data.value = null;
}

function handleShowingInput() {
  if (oldValue.value !== null) {
    data.value = oldValue.value;
  }
}

function uploadStart() {
  emit("uploadstart");
}

function uploadEnd() {
  emit("uploadend");
}
</script>
