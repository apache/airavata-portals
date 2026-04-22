<template>
  <div class="card">
    <div class="card-header d-flex align-items-center">
      <div class="me-auto">Output Field: {{ data.name }}</div>
      <a v-if="!readonly" class="text-secondary" @click="deleteApplicationOutput">
        <i class="fa fa-trash"></i>
        <span class="visually-hidden">Delete</span>
      </a>
    </div>
    <div class="card-body">
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
      <div class="mb-3" label="Value" :label-for="id + '-value'">
        <input
          :id="id + '-value'"
          v-model="data.value"
          class="form-control"
          type="text"
          :disabled="readonly"
        />
      </div>
      <div class="mb-3" label="Type" :label-for="id + '-type'">
        <select
          :id="id + '-type'"
          v-model="data.type"
          class="form-select"
          :options="outputTypeOptions"
          :disabled="readonly"
        />
      </div>
      <div class="mb-3" label="Application Argument" :label-for="id + '-argument'">
        <input
          :id="id + '-argument'"
          v-model="data.applicationArgument"
          class="form-control"
          type="text"
          :disabled="readonly"
        />
      </div>
      <div class="d-flex">
        <form-group class="flex-fill" label="Is Required" :label-for="id + '-required'">
          <form-radio-group
            :id="id + '-required'"
            v-model="data.isRequired"
            :options="trueFalseOptions"
            :disabled="readonly"
          />
        </form-group>
        <form-group
          class="flex-fill"
          label="Required on Command Line"
          :label-for="id + '-required-command-line'"
        >
          <form-radio-group
            :id="id + '-required-command-line'"
            v-model="data.requiredToAddedToCommandLine"
            :options="trueFalseOptions"
            :disabled="readonly"
          />
        </form-group>
      </div>
      <form-group
        label="Metadata"
        :label-for="id + '-metadata'"
        description="Metadata for this output, in the JSON format"
      >
        <json-editor
          :id="id + '-metadata'"
          v-model="data.metaData"
          :rows="5"
          :disabled="readonly"
        />
      </form-group>
      <button class="btn" size="sm" @click="setPlainText">Plain Text</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models } from "django-airavata-api";
import JsonEditor from "./JSONEditor.vue";

type OutputDataObjectType = InstanceType<typeof models.OutputDataObjectType>;

const props = defineProps<{
  modelValue: OutputDataObjectType;
  focus?: boolean;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: OutputDataObjectType];
  delete: [];
}>();

const nameInput = ref<HTMLInputElement | null>(null);

const data = ref<OutputDataObjectType>(
  props.modelValue.clone() as OutputDataObjectType,
);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue.clone() as OutputDataObjectType;
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

const outputTypeOptions = computed(() =>
  (models.OutputDataObjectType.VALID_DATA_TYPES as Array<{ name: string }>).map((dataType) => ({
    value: dataType,
    text: dataType.name,
  })),
);

const trueFalseOptions = computed(() => [
  { text: "True", value: true },
  { text: "False", value: false },
]);

const id = computed(() => "id-" + (data.value as { key: string }).key);

onMounted(() => {
  if (props.focus) {
    nameInput.value?.focus();
  }
});

function deleteApplicationOutput() {
  emit("delete");
}

function setPlainText() {
  const metadata = ((data.value as { metaData?: Record<string, unknown> }).metaData || {}) as Record<string, unknown>;
  metadata["file-metadata"] = { "mime-type": "text/plain" };
  // Clone so that JSONEditor updates with new value
  (data.value as { metaData: Record<string, unknown> }).metaData = JSON.parse(JSON.stringify(metadata)) as Record<string, unknown>;
}
</script>
