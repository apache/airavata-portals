/**
 * useInputEditor — composable that inlines the InputEditorMixin functionality.
 *
 * Provides the same data, computed, watch, and lifecycle as InputEditorMixin but
 * in composable form so <script setup lang="ts"> components can use it directly.
 */
import { ref, computed, watch, onMounted } from "vue";
import { models } from "django-airavata-api";

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;

export interface InputEditorProps {
  modelValue?: string | null;
  experimentInput: InputDataObjectType;
  experiment?: Experiment;
  id: string;
  readOnly?: boolean;
}

export type InputEditorEmits = {
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
};

export function useInputEditor(
  props: InputEditorProps,
  emit: (event: "update:modelValue", value: string | null) => void,
  emitValid: () => void,
  emitInvalid: (messages: string[]) => void,
) {
  const data = ref<string | null>(props.modelValue ?? null);
  const inputHasBegun = ref(false);
  const validationMessages = ref<string[]>([]);
  const valid = ref(false);
  const componentValidState = ref<boolean | null>(null);

  const editorConfig = computed(() => props.experimentInput.editorConfig);

  watch(
    () => props.modelValue,
    (newVal) => {
      data.value = newVal ?? null;
    },
  );

  watch(data, () => {
    updateValidation();
  });

  function valueChanged() {
    inputHasBegun.value = true;
    emit("update:modelValue", data.value);
  }

  function checkValidation() {
    if (valid.value) {
      emitValid();
    } else {
      emitInvalid(validationMessages.value);
    }
  }

  async function updateValidation() {
    const results = props.experimentInput.validate(data.value);
    let value: string[] = [];
    if ("value" in results) {
      value = await Promise.all(results["value"]).then((arr: (string | null)[]) =>
        arr.filter((x): x is string => x !== null),
      );
    }
    validationMessages.value = value;
    valid.value = value.length === 0;
    componentValidState.value = inputHasBegun.value ? valid.value : null;
    checkValidation();
  }

  onMounted(() => {
    updateValidation();
  });

  return {
    data,
    inputHasBegun,
    validationMessages,
    valid,
    componentValidState,
    editorConfig,
    valueChanged,
    updateValidation,
  };
}
