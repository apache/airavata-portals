<template>
  <div class="card">
    <div class="card-header d-flex align-items-center">
      <div v-if="!readonly" class="drag-handle me-1 text-muted">
        <i class="fa fa-grip-vertical"></i>
        <span class="visually-hidden">Drag handle for reordering</span>
      </div>
      <div class="me-auto">Input Field: {{ data.name }}</div>
      <a v-if="!readonly" class="text-secondary" @click="deleteApplicationInput">
        <i class="fa fa-trash"></i>
        <span class="visually-hidden">Delete</span>
      </a>
    </div>
    <div class="card-body">
      <div :id="id + '-collapse'" class="collapse" :visible="!collapse">
        <div class="mb-3" label="Name" :label-for="id + '-name'">
          <input
            :id="id + '-name'"
            ref="nameInput"
            v-model="data.name"
            class="form-control"
            type="text"
            required
            :disabled="readonly"
          />
        </div>
        <div class="mb-3" label="Type" :label-for="id + '-type'">
          <select
            :id="id + '-type'"
            v-model="data.type"
            class="form-select"
            :options="inputTypeOptions"
            :disabled="readonly"
          />
        </div>
        <form-group v-if="showValueField" label="Initial Value" :label-for="id + '-value'">
          <input
            :id="id + '-value'"
            v-model="data.value"
            class="form-control"
            type="text"
            :disabled="readonly"
          />
        </form-group>
        <form-group
          v-if="showOverrideFilenameField"
          label="Override Filename"
          :label-for="id + '-value'"
        >
          <input
            :id="id + '-override-filename'"
            v-model="data.overrideFilename"
            class="form-control"
            type="text"
            :disabled="readonly"
          />
        </form-group>
        <div class="mb-3" label="Application Argument" :label-for="id + '-argument'">
          <input
            :id="id + '-argument'"
            v-model="data.applicationArgument"
            class="form-control"
            type="text"
            :disabled="readonly"
          />
        </div>
        <form-group
          class="flex-fill"
          label="Required on Command Line"
          :label-for="id + '-required-command-line'"
          description="Add this input's value to the command line in the generated job script."
        >
          <form-radio-group
            :id="id + '-required-command-line'"
            v-model="data.requiredToAddedToCommandLine"
            :options="trueFalseOptions"
            :disabled="readonly"
          />
        </form-group>
        <div class="d-flex">
          <form-group class="flex-fill" label="Required" :label-for="id + '-required'">
            <form-radio-group
              :id="id + '-required'"
              v-model="data.isRequired"
              :options="trueFalseOptions"
              :disabled="readonly"
            />
          </form-group>
          <form-group class="flex-fill" label="Read Only" :label-for="id + '-read-only'">
            <form-radio-group
              :id="id + '-read-only'"
              v-model="data.isReadOnly"
              :options="trueFalseOptions"
              :disabled="readonly"
            />
          </form-group>
        </div>
        <form-group
          label="User Friendly Description"
          :label-for="id + '-user-friendly-description'"
        >
          <textarea
            :id="id + '-user-friendly-description'"
            v-model="data.userFriendlyDescription"
            class="form-control"
            :rows="3"
            :disabled="readonly"
          />
        </form-group>
        <form-group
          label="Advanced Input Field Modification Metadata"
          :label-for="id + '-metadata'"
          description="Metadata for this input, in the JSON format"
        >
          <json-editor
            :id="id + '-metadata'"
            v-model="data.metaData"
            :rows="5"
            :disabled="readonly"
          />
        </form-group>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models } from "django-airavata-api";
import JsonEditor from "./JSONEditor.vue";

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;

const props = defineProps<{
  modelValue: InputDataObjectType;
  // Whether to put focus on the name field when mounting component
  focus?: boolean;
  collapse?: boolean;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: InputDataObjectType];
  delete: [];
}>();

const nameInput = ref<HTMLInputElement | null>(null);

const data = ref<InputDataObjectType>(
  props.modelValue.clone() as InputDataObjectType,
);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue.clone() as InputDataObjectType;
  },
  { deep: true },
);

watch(
  data,
  (newValue, oldValue) => {
    if (newValue === oldValue) {
      emit("update:modelValue", newValue);
    }
  },
  { deep: true },
);

const inputTypeOptions = computed(() =>
  (models.InputDataObjectType.VALID_DATA_TYPES as Array<{ name: string }>).map((dataType) => ({
    value: dataType,
    text: dataType.name,
  })),
);

const trueFalseOptions = computed(() => [
  { text: "True", value: true },
  { text: "False", value: false },
]);

const id = computed(() => "id-" + (data.value as { key: string }).key);

const showValueField = computed(() =>
  (data.value as { type?: { isSimpleValueType?: boolean } }).type?.isSimpleValueType,
);

const showOverrideFilenameField = computed(
  () => (data.value as { type?: unknown }).type === models.DataType?.URI,
);

onMounted(() => {
  if (props.focus) {
    nameInput.value?.focus();
  }
});

function deleteApplicationInput() {
  emit("delete");
}
</script>

<style scoped>
.drag-handle {
  cursor: move;
}
</style>
