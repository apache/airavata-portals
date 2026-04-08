<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Application Interface</h1>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <form-group
          label="Enable Archiving Working Directory"
          label-for="archive-directory"
        >
          <form-radio-group
            id="archive-directory"
            v-model="data.archiveWorkingDirectory"
            :options="trueFalseOptions"
            :disabled="readonly"
          >
          </div>
        </div>
      </div>
      <div class="col">
        <form-group
          label="Show Queue Settings"
          label-for="show-queue-settings"
        >
          <form-radio-group
            id="show-queue-settings"
            v-model="data.showQueueSettings"
            :options="trueFalseOptions"
            :disabled="readonly"
          >
          </div>
          <div slot="description">
            Show a queue selector along with queue related settings (nodes,
            cores, walltime limit).
          </div>
        </div>
        <form-group
          label="Queue Settings Calculator"
          description="Select function to automatically compute queue settings."
        >
          <select class="form-select"
            v-model="data.queueSettingsCalculatorId"
            :options="queueSettingsCalculatorOptions"
            :disabled="queueSettingsCalculatorOptions.length === 0"
          >
            <template slot="first">
              <option :value="null">
                If applicable, select a queue settings calculator
              </option>
            </template>
          </select>
        </div>
      </div>
    </div>
    <div class="w-100">
      <form-group
        label="Application Instructions"
        label-for="application-description"
      >
        <textarea class="form-control"
          id="application-description"
          :rows="5"
          v-model="data.applicationDescription"
          :state="
            !data.applicationDescription ||
            data.applicationDescription.length < 500
          "
        >
        </textarea>
        <form-valid-feedback v-if="!!data.applicationDescription">
          {{ data.applicationDescription.length }} / 500
        </div>
        <div class="invalid-feedback">
          Application instructions text is limited to 500 characters maximum.
        </div>
      </div>
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
            :value="input"
            :key="input.key"
            :focus="input.key === focusApplicationInputKey"
            :collapse="collapseApplicationInputs"
            @input="updatedInput"
            @delete="deleteInput(input)"
            :readonly="readonly"
          />
        </draggable>
      </div>
    </div>
    <div class="row mb-4">
      <div class="col">
        <button class="btn"
          variant="secondary"
          @click="addApplicationInput"
          :disabled="readonly"
        >
          Add application input
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <h1 class="h5 mb-4">Output Fields</h1>
        <application-output-field-editor
          v-for="output in data.applicationOutputs"
          :value="output"
          :key="output.key"
          :focus="output.key === focusApplicationOutputKey"
          @input="updatedOutput"
          @delete="deleteOutput(output)"
          :readonly="readonly"
        />
      </div>
    </div>
    <div class="row mb-4">
      <div class="col">
        <button class="btn"
          variant="secondary"
          @click="addApplicationOutput"
          :disabled="readonly"
        >
          Add application output
        </button>
      </div>
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
      dragOptions: {
        handle: ".drag-handle",
      },
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
      const input = this.data.applicationInputs.find(
        (input) => input.key === newValue.key
      );
      Object.assign(input, newValue);
    },
    addApplicationInput() {
      const appInput = new models.InputDataObjectType();
      this.data.applicationInputs.push(appInput);
      this.focusApplicationInputKey = appInput.key;
    },
    deleteInput(input) {
      const inputIndex = this.data.applicationInputs.findIndex(
        (inp) => inp.key === input.key
      );
      this.data.applicationInputs.splice(inputIndex, 1);
    },
    updatedOutput(newValue) {
      const output = this.data.applicationOutputs.find(
        (o) => o.key === newValue.key
      );
      Object.assign(output, newValue);
    },
    addApplicationOutput() {
      const newOutput = new models.OutputDataObjectType();
      this.data.applicationOutputs.push(newOutput);
      this.focusApplicationOutputKey = newOutput.key;
    },
    deleteOutput(output) {
      const outputIndex = this.data.applicationOutputs.findIndex(
        (o) => o.key === output.key
      );
      this.data.applicationOutputs.splice(outputIndex, 1);
    },
    onDragStart() {
      this.collapseApplicationInputs = true;
    },
    onDragEnd() {
      this.collapseApplicationInputs = false;
    },
    async loadQueueSettingsCalculators() {
      this.queueSettingsCalculators = await services.QueueSettingsCalculatorService.list();
    },
  },
};
</script>
