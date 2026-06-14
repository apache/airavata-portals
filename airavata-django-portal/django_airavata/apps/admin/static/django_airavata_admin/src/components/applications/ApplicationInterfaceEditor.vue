<template>
  <div>
    <div>
      <h2 class="mb-4 text-lg font-semibold">Application Interface</h2>
    </div>
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div>
        <div class="space-y-1.5">
          <Label>Enable Archiving Working Directory</Label>
          <div class="flex gap-4">
            <label
              v-for="opt in trueFalseOptions"
              :key="String(opt.value)"
              class="flex items-center gap-2 text-sm"
            >
              <input
                type="radio"
                :value="opt.value"
                v-model="data.archive_working_directory"
                :disabled="readonly"
              />
              {{ opt.text }}
            </label>
          </div>
        </div>
      </div>
      <div class="space-y-4">
        <div class="space-y-1.5">
          <Label>Show Queue Settings</Label>
          <div class="flex gap-4">
            <label
              v-for="opt in trueFalseOptions"
              :key="String(opt.value)"
              class="flex items-center gap-2 text-sm"
            >
              <input
                type="radio"
                :value="opt.value"
                v-model="data.show_queue_settings"
                :disabled="readonly"
              />
              {{ opt.text }}
            </label>
          </div>
          <p class="text-sm text-muted-foreground">
            Show a queue selector along with queue related settings (nodes,
            cores, walltime limit).
          </p>
        </div>
        <div class="space-y-1.5">
          <Label>Queue Settings Calculator</Label>
          <select
            v-model="data.queue_settings_calculator_id"
            :disabled="queueSettingsCalculatorOptions.length === 0"
            class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option :value="null">
              If applicable, select a queue settings calculator
            </option>
            <option
              v-for="opt in queueSettingsCalculatorOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.text }}
            </option>
          </select>
          <p class="text-sm text-muted-foreground">
            Select function to automatically compute queue settings.
          </p>
        </div>
      </div>
    </div>
    <div class="mt-4 w-full">
      <div class="space-y-1.5">
        <Label for="application-description">Application Instructions</Label>
        <Textarea
          id="application-description"
          :rows="5"
          v-model="data.application_description"
          :aria-invalid="descriptionTooLong"
        >
        </Textarea>
        <p
          v-if="!!data.application_description && !descriptionTooLong"
          class="text-sm text-muted-foreground"
        >
          {{ data.application_description.length }} / 500
        </p>
        <p v-if="descriptionTooLong" class="text-sm text-destructive">
          Application instructions text is limited to 500 characters maximum.
        </p>
      </div>
    </div>
    <div class="mt-4">
      <h2 class="mb-4 text-lg font-semibold">Input Fields</h2>
      <draggable
        v-model="data.application_inputs"
        item-key="key"
        handle=".drag-handle"
        @start="onDragStart"
        @end="onDragEnd"
      >
        <template #item="{ element: input }">
          <application-input-field-editor
            :value="input"
            :focus="input.key === focusApplicationInputKey"
            :collapse="collapseApplicationInputs"
            @input="updatedInput"
            @delete="deleteInput(input)"
            :readonly="readonly"
          />
        </template>
      </draggable>
    </div>
    <div class="my-4">
      <Button
        variant="secondary"
        @click="addApplicationInput"
        :disabled="readonly"
      >
        Add application input
      </Button>
    </div>
    <div>
      <h2 class="mb-4 text-lg font-semibold">Output Fields</h2>
      <application-output-field-editor
        v-for="output in data.application_outputs"
        :value="output"
        :key="output.key"
        :focus="output.key === focusApplicationOutputKey"
        @input="updatedOutput"
        @delete="deleteOutput(output)"
        :readonly="readonly"
      />
    </div>
    <div class="my-4">
      <Button
        variant="secondary"
        @click="addApplicationOutput"
        :disabled="readonly"
      >
        Add application output
      </Button>
    </div>
  </div>
</template>

<script>
import { models, services } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";
import ApplicationInputFieldEditor from "./ApplicationInputFieldEditor.vue";
import ApplicationOutputFieldEditor from "./ApplicationOutputFieldEditor.vue";

import draggable from "vuedraggable";

export default {
  name: "application-interface-editor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.ApplicationInterfaceDefinition,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  components: {
    ApplicationInputFieldEditor,
    ApplicationOutputFieldEditor,
    draggable,
  },
  created() {
    this.loadQueueSettingsCalculators();
  },
  computed: {
    trueFalseOptions() {
      return [
        { text: "True", value: true },
        { text: "False", value: false },
      ];
    },
    descriptionTooLong() {
      return (
        !!this.data.application_description &&
        this.data.application_description.length >= 500
      );
    },
    queueSettingsCalculatorOptions() {
      if (this.queueSettingsCalculators) {
        return this.queueSettingsCalculators.map((qsc) => {
          return {
            text: qsc.name,
            value: qsc.id,
          };
        });
      } else {
        return [];
      }
    },
  },
  data() {
    return {
      focusApplicationInputKey: null,
      focusApplicationOutputKey: null,
      collapseApplicationInputs: false,
      queueSettingsCalculators: null,
    };
  },
  methods: {
    save() {
      this.$emit("save");
    },
    cancel() {
      this.$emit("cancel");
    },
    updatedInput(newValue) {
      const input = this.data.application_inputs.find(
        (input) => input.key === newValue.key,
      );
      Object.assign(input, newValue);
    },
    addApplicationInput() {
      const appInput = new models.InputDataObjectType();
      this.data.application_inputs.push(appInput);
      this.focusApplicationInputKey = appInput.key;
    },
    deleteInput(input) {
      const inputIndex = this.data.application_inputs.findIndex(
        (inp) => inp.key === input.key,
      );
      this.data.application_inputs.splice(inputIndex, 1);
    },
    updatedOutput(newValue) {
      const output = this.data.application_outputs.find(
        (o) => o.key === newValue.key,
      );
      Object.assign(output, newValue);
    },
    addApplicationOutput() {
      const newOutput = new models.OutputDataObjectType();
      this.data.application_outputs.push(newOutput);
      this.focusApplicationOutputKey = newOutput.key;
    },
    deleteOutput(output) {
      const outputIndex = this.data.application_outputs.findIndex(
        (o) => o.key === output.key,
      );
      this.data.application_outputs.splice(outputIndex, 1);
    },
    onDragStart() {
      this.collapseApplicationInputs = true;
    },
    onDragEnd() {
      this.collapseApplicationInputs = false;
    },
    async loadQueueSettingsCalculators() {
      this.queueSettingsCalculators =
        await services.QueueSettingsCalculatorService.list();
    },
  },
};
</script>
