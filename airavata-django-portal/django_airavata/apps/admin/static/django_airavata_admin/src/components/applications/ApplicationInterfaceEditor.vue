<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Application Interface</h1>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <form-group label="Enable Archiving Working Directory" label-for="archive-directory">
          <form-radio-group
            id="archive-directory"
            v-model="data.archiveWorkingDirectory"
            :options="trueFalseOptions"
            :disabled="readonly"
          />
        </form-group>
      </div>
      <div class="col">
        <form-group
          label="Show Queue Settings"
          label-for="show-queue-settings"
          description="Show a queue selector along with queue related settings (nodes, cores, walltime limit)."
        >
          <form-radio-group
            id="show-queue-settings"
            v-model="data.showQueueSettings"
            :options="trueFalseOptions"
            :disabled="readonly"
          />
        </form-group>
        <form-group
          label="Queue Settings Calculator"
          description="Select function to automatically compute queue settings."
        >
          <select
            v-model="data.queueSettingsCalculatorId"
            class="form-select"
            :disabled="queueSettingsCalculatorOptions.length === 0"
          >
            <option :value="null">If applicable, select a queue settings calculator</option>
            <option
              v-for="opt in queueSettingsCalculatorOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.text }}
            </option>
          </select>
        </form-group>
      </div>
    </div>
    <div class="w-100">
      <form-group label="Application Instructions" label-for="application-description">
        <textarea
          id="application-description"
          v-model="data.applicationDescription"
          class="form-control"
          :rows="5"
        >
        </textarea>
        <small v-if="!!data.applicationDescription" class="form-text text-muted">
          {{ data.applicationDescription.length }} / 500
        </small>
        <div
          v-if="data.applicationDescription && data.applicationDescription.length >= 500"
          class="invalid-feedback"
        >
          Application instructions text is limited to 500 characters maximum.
        </div>
      </form-group>
    </div>
    <div class="row">
      <div class="col">
        <h1 class="h5 mb-4">Input Fields</h1>
        <draggable
          v-model="data.applicationInputs"
          :options="dragOptions"
          @start="onDragStart"
          @end="onDragEnd"
        >
          <application-input-field-editor
            v-for="input in data.applicationInputs"
            :key="input.key"
            :model-value="input"
            :focus="input.key === focusApplicationInputKey"
            :collapse="collapseApplicationInputs"
            :readonly="readonly"
            @update:model-value="updatedInput"
            @delete="deleteInput(input)"
          />
        </draggable>
      </div>
    </div>
    <div class="row mb-4">
      <div class="col">
        <button class="btn btn-secondary btn-sm" :disabled="readonly" @click="addApplicationInput">
          Add application input
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <h1 class="h5 mb-4">Output Fields</h1>
        <application-output-field-editor
          v-for="output in data.applicationOutputs"
          :key="output.key"
          :model-value="output"
          :focus="output.key === focusApplicationOutputKey"
          :readonly="readonly"
          @update:model-value="updatedOutput"
          @delete="deleteOutput(output)"
        />
      </div>
    </div>
    <div class="row mb-4">
      <div class="col">
        <button class="btn btn-secondary btn-sm" :disabled="readonly" @click="addApplicationOutput">
          Add application output
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models, services } from "django-airavata-api";
import ApplicationInputFieldEditor from "./ApplicationInputFieldEditor.vue";
import ApplicationOutputFieldEditor from "./ApplicationOutputFieldEditor.vue";
import draggable from "vuedraggable";

type AppInterface = InstanceType<typeof models.ApplicationInterfaceDefinition>;

const props = defineProps<{
  modelValue: AppInterface;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: AppInterface];
}>();

const focusApplicationInputKey = ref<string | null>(null);
const focusApplicationOutputKey = ref<string | null>(null);
const dragOptions = { handle: ".drag-handle" };
const collapseApplicationInputs = ref(false);
const queueSettingsCalculators = ref<Array<{ id: string; name: string }> | null>(null);

const data = ref<AppInterface>(
  props.modelValue.clone() as AppInterface,
);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue.clone() as AppInterface;
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

const trueFalseOptions = computed(() => [
  { text: "True", value: true },
  { text: "False", value: false },
]);

const queueSettingsCalculatorOptions = computed(() => {
  if (queueSettingsCalculators.value) {
    return queueSettingsCalculators.value.map((qsc) => ({
      text: qsc.name,
      value: qsc.id,
    }));
  } else {
    return [];
  }
});

onMounted(async () => {
  queueSettingsCalculators.value = await services.QueueSettingsCalculatorService.list() as Array<{ id: string; name: string }>;
});

function updatedInput(newValue: unknown) {
  const inputField = newValue as { key: string };
  const input = (data.value as { applicationInputs: Array<{ key: string }> }).applicationInputs.find(
    (inp) => inp.key === inputField.key,
  );
  if (input) Object.assign(input, newValue);
}

function addApplicationInput() {
  const appInput = new models.InputDataObjectType();
  (data.value as { applicationInputs: unknown[] }).applicationInputs.push(appInput);
  focusApplicationInputKey.value = (appInput as { key: string }).key;
}

function deleteInput(input: unknown) {
  const inputKey = (input as { key: string }).key;
  const inputsArr = (data.value as { applicationInputs: Array<{ key: string }> }).applicationInputs;
  const inputIndex = inputsArr.findIndex((inp) => inp.key === inputKey);
  inputsArr.splice(inputIndex, 1);
}

function updatedOutput(newValue: unknown) {
  const outputField = newValue as { key: string };
  const output = (data.value as { applicationOutputs: Array<{ key: string }> }).applicationOutputs.find(
    (o) => o.key === outputField.key,
  );
  if (output) Object.assign(output, newValue);
}

function addApplicationOutput() {
  const newOutput = new models.OutputDataObjectType();
  (data.value as { applicationOutputs: unknown[] }).applicationOutputs.push(newOutput);
  focusApplicationOutputKey.value = (newOutput as { key: string }).key;
}

function deleteOutput(output: unknown) {
  const outputKey = (output as { key: string }).key;
  const outputsArr = (data.value as { applicationOutputs: Array<{ key: string }> }).applicationOutputs;
  const outputIndex = outputsArr.findIndex((o) => o.key === outputKey);
  outputsArr.splice(outputIndex, 1);
}

function onDragStart() {
  collapseApplicationInputs.value = true;
}

function onDragEnd() {
  collapseApplicationInputs.value = false;
}
</script>
