<template>
  <div>
    <div v-for="dataProductURI in selectedDataProductURIs" :key="dataProductURI" class="mb-2">
      <FileInputEditor
        :id="dataProductURI"
        :value="dataProductURI"
        :experiment="experiment"
        :experiment-input="experimentInput"
        :read-only="readOnly"
        @input="updatedFile($event, dataProductURI)"
      />
    </div>
    <InputFileSelector
      v-if="!readOnly"
      :selected-data-product-u-r-is="selectedDataProductURIs"
      multiple
      @selected="fileSelected"
      @uploadstart="emit('uploadstart')"
      @uploadend="emit('uploadend')"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { models } from "django-airavata-api";
import { useInputEditor } from "@/composables/useInputEditor";
import FileInputEditor from "./FileInputEditor.vue";
import InputFileSelector from "./InputFileSelector.vue";

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    experimentInput: InputDataObjectType;
    experiment?: Experiment;
    id: string;
    readOnly?: boolean;
  }>(),
  { modelValue: null, experiment: undefined, readOnly: false },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
  uploadstart: [];
  uploadend: [];
}>();

const { data, valueChanged } = useInputEditor(
  props,
  (_, v) => emit("update:modelValue", v),
  () => emit("valid"),
  (msgs) => emit("invalid", msgs),
);

const selectedDataProductURIs = computed(() => createValueArray(data.value));

function updatedFile(newValue: string | null, dataProductURI: string) {
  if (!newValue) {
    removeFile(dataProductURI);
  }
}

function removeFile(dataProductURI: string) {
  const index = selectedDataProductURIs.value.findIndex((u) => u === dataProductURI);
  const copyDataProductURIs = selectedDataProductURIs.value.slice();
  copyDataProductURIs.splice(index, 1);
  data.value = copyDataProductURIs.join(",");
  valueChanged();
}

function createValueArray(value: string | null): string[] {
  if (value && typeof value === "string") {
    return value.split(",");
  } else {
    return [];
  }
}

function fileSelected(dataProductURI: string) {
  const values = createValueArray(data.value);
  values.push(dataProductURI);
  data.value = values.join(",");
  valueChanged();
}
</script>
