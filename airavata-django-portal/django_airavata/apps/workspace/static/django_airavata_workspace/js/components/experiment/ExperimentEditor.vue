<template>
  <main-layout>
    <template #title>
      <h1 class="text-2xl font-semibold tracking-tight text-foreground">
        <slot name="title">Experiment Editor</slot>
      </h1>
      <p
        v-if="appModule"
        class="mt-1 inline-flex items-center gap-1 text-sm text-muted-foreground uppercase"
      >
        <CodeIcon class="size-4" aria-hidden="true" />
        {{ appModule.app_module_name }}
      </p>
    </template>
    <template #actions>
      <share-button
        ref="shareButton"
        :entity-id="localExperiment.experiment_id"
        :entity-label="'Experiment'"
        :parent-entity-id="localExperiment.project_id"
        :parent-entity-label="'Project'"
        :auto-add-default-gateway-users-group="false"
      />
    </template>
    <unsaved-changes-guard :dirty="dirty" />
    <form novalidate>
      <div class="mb-4">
        <div class="space-y-1.5">
          <Label for="experiment-name">Experiment Name</Label>
          <Input
            id="experiment-name"
            type="text"
            v-model="localExperiment.experiment_name"
            required
            placeholder="Experiment name"
            :aria-invalid="getValidationState('experiment_name') === false"
          />
          <p
            v-if="getValidationState('experiment_name') === false"
            class="text-sm text-destructive"
          >
            {{ getValidationFeedback("experiment_name") }}
          </p>
        </div>
        <experiment-description-editor v-model="localExperiment.description" />
      </div>
      <div class="mb-4">
        <div class="space-y-1.5">
          <Label for="project">Project</Label>
          <select
            id="project"
            v-model="localExperiment.project_id"
            required
            :aria-invalid="getValidationState('project_id') === false"
            :class="nativeSelectClass"
          >
            <option :value="null" disabled>Select a Project</option>
            <optgroup label="My Projects">
              <option
                v-for="project in myProjectOptions"
                :value="project.value"
                :key="project.value"
              >
                {{ project.text }}
              </option>
            </optgroup>
            <optgroup label="Projects Shared With Me">
              <option
                v-for="project in sharedProjectOptions"
                :value="project.value"
                :key="project.value"
              >
                {{ project.text }}
              </option>
            </optgroup>
          </select>
          <p
            v-if="getValidationState('project_id') === false"
            class="text-sm text-destructive"
          >
            {{ getValidationFeedback("project_id") }}
          </p>
        </div>
      </div>
      <div>
        <workspace-notices-management-container
          class="mt-2"
          v-if="appInterface && appInterface.application_description"
          :data="[
            { notification_message: appInterface.application_description },
          ]"
        />
      </div>
      <div>
        <h2 class="mt-2 mb-4 text-lg font-semibold">
          Application Configuration
        </h2>
      </div>
      <div>
        <Card>
          <CardContent>
            <h2 class="mb-3 text-base font-semibold">Application Inputs</h2>

            <transition-group name="fade">
              <input-editor-container
                v-for="experimentInput in localExperiment.experiment_inputs"
                :experiment-input="experimentInput"
                :experiment="localExperiment"
                v-model="experimentInput.value"
                v-show="experimentInput.show"
                :key="experimentInput.name"
                @invalid="recordInvalidInputEditorValue(experimentInput.name)"
                @valid="recordValidInputEditorValue(experimentInput.name)"
                @input="inputValueChanged"
                @uploadstart="uploadStart(experimentInput.name)"
                @uploadend="uploadEnd(experimentInput.name)"
              />
            </transition-group>
          </CardContent>
        </Card>
      </div>
      <div class="mt-4">
        <group-resource-profile-selector
          v-model="
            localExperiment.user_configuration_data.group_resource_profile_id
          "
          @invalid="invalidGroupResourceProfileSelector = true"
          @valid="invalidGroupResourceProfileSelector = false"
        >
        </group-resource-profile-selector>
      </div>
      <div class="mt-4">
        <computational-resource-scheduling-editor
          v-model="
            localExperiment.user_configuration_data
              .computational_resource_scheduling
          "
          v-if="
            localExperiment.user_configuration_data.group_resource_profile_id
          "
          :app-module-id="appModule.app_module_id"
          :group-resource-profile-id="
            localExperiment.user_configuration_data.group_resource_profile_id
          "
          @invalid="invalidComputationalResourceSchedulingEditor = true"
          @valid="invalidComputationalResourceSchedulingEditor = false"
        >
        </computational-resource-scheduling-editor>
      </div>
      <div class="mt-4">
        <div class="space-y-1.5">
          <Label>Email Settings</Label>
          <Label class="font-normal">
            <Checkbox v-model="localExperiment.enable_email_notification" />
            Receive email notification of experiment status
          </Label>
        </div>
      </div>
      <div class="mt-4 flex justify-end gap-2">
        <Button
          variant="secondary"
          @click="saveExperiment"
          :disabled="isSaveDisabled"
        >
          Save
        </Button>
        <Button
          variant="default"
          @click="saveAndLaunchExperiment"
          :disabled="isSaveDisabled"
        >
          Save and Launch
        </Button>
      </div>
    </form>
  </main-layout>
</template>

<script>
import { Code as CodeIcon } from "@lucide/vue";
import ComputationalResourceSchedulingEditor from "./ComputationalResourceSchedulingEditor.vue";
import ExperimentDescriptionEditor from "./ExperimentDescriptionEditor.vue";
import GroupResourceProfileSelector from "./GroupResourceProfileSelector.vue";
import InputEditorContainer from "./input-editors/InputEditorContainer.vue";
import { models, services } from "django-airavata-api";
import { components, utils } from "django-airavata-common-ui";
import WorkspaceNoticesManagementContainer from "../notices/WorkspaceNoticesManagementContainer";
import { NATIVE_SELECT_CLASS } from "../../lib/utils";
import { useDebounceFn } from "@vueuse/core";

export default {
  name: "edit-experiment",
  props: {
    experiment: {
      type: models.Experiment,
      required: true,
    },
    appModule: {
      type: models.ApplicationModule,
      required: true,
    },
    appInterface: {
      type: models.ApplicationInterfaceDefinition,
      required: true,
    },
  },
  data() {
    return {
      projects: [],
      localExperiment: this.experiment.clone(),
      invalidInputs: [],
      invalidComputationalResourceSchedulingEditor: false,
      invalidGroupResourceProfileSelector: false,
      edited: false,
      saved: false,
      uploadingInputs: [],
    };
  },
  components: {
    CodeIcon,
    WorkspaceNoticesManagementContainer,
    ComputationalResourceSchedulingEditor,
    ExperimentDescriptionEditor,
    GroupResourceProfileSelector,
    InputEditorContainer,
    "main-layout": components.MainLayout,
    "share-button": components.ShareButton,
    "unsaved-changes-guard": components.UnsavedChangesGuard,
  },
  mounted: function () {
    services.ProjectService.listAll().then((projects) => {
      this.projects = projects;
      if (!this.localExperiment.project_id) {
        services.WorkspacePreferencesService.get().then(
          (workspacePreferences) => {
            if (!this.localExperiment.project_id) {
              this.localExperiment.project_id =
                workspacePreferences.most_recent_project_id;
            }
          },
        );
      }
    });
  },
  computed: {
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>, plus the
      // invalid-state ring so it mirrors `:aria-invalid` on shadcn controls.
      return `${NATIVE_SELECT_CLASS} aria-invalid:border-destructive aria-invalid:ring-destructive/40`;
    },
    sharedProjectOptions: function () {
      return this.projects
        .filter((p) => !p.is_owner)
        .map((project) => ({
          value: project.project_id,
          text:
            project.name +
            (!project.is_owner ? " (owned by " + project.owner + ")" : ""),
        }));
    },
    myProjectOptions() {
      return this.projects
        .filter((p) => p.is_owner)
        .map((project) => ({
          value: project.project_id,
          text: project.name,
        }));
    },
    valid: function () {
      const validation = this.localExperiment.validate();
      return (
        Object.keys(validation).length === 0 &&
        this.invalidInputs.length === 0 &&
        !this.invalidComputationalResourceSchedulingEditor &&
        !this.invalidGroupResourceProfileSelector
      );
    },
    isSaveDisabled: function () {
      return !this.valid || this.hasUploadingInputs;
    },
    dirty() {
      return this.edited && !this.saved;
    },
    hasUploadingInputs() {
      return this.uploadingInputs.length > 0;
    },
  },
  methods: {
    saveExperiment: function () {
      return this.saveOrUpdateExperiment().then((experiment) => {
        this.localExperiment = experiment;
        this.$emit("saved", experiment);
      });
    },
    saveAndLaunchExperiment: function () {
      return this.saveOrUpdateExperiment().then((experiment) => {
        this.localExperiment = experiment;
        return services.ExperimentService.launch({
          lookup: experiment.experiment_id,
        }).then(() => {
          this.$emit("savedAndLaunched", experiment);
        });
      });
    },
    saveOrUpdateExperiment: function () {
      if (this.localExperiment.experiment_id) {
        return services.ExperimentService.update({
          lookup: this.localExperiment.experiment_id,
          data: this.localExperiment,
        }).then((experiment) => {
          this.saved = true;
          return experiment;
        });
      } else {
        return services.ExperimentService.create({
          data: this.localExperiment,
        }).then((experiment) => {
          // Can't save sharing settings for a new experiment until it has been
          // created
          this.saved = true;
          return this.$refs.shareButton
            .mergeAndSave(experiment.experiment_id)
            .then(() => experiment);
        });
      }
    },
    getValidationFeedback: function (properties) {
      return utils.getProperty(this.localExperiment.validate(), properties);
    },
    getValidationState: function (properties) {
      return this.getValidationFeedback(properties) ? false : null;
    },
    recordInvalidInputEditorValue: function (experimentInputName) {
      if (!this.invalidInputs.includes(experimentInputName)) {
        this.invalidInputs.push(experimentInputName);
      }
    },
    recordValidInputEditorValue: function (experimentInputName) {
      if (this.invalidInputs.includes(experimentInputName)) {
        const index = this.invalidInputs.indexOf(experimentInputName);
        this.invalidInputs.splice(index, 1);
      }
    },
    uploadStart(experimentInputName) {
      if (!this.uploadingInputs.includes(experimentInputName)) {
        this.uploadingInputs.push(experimentInputName);
      }
    },
    uploadEnd(experimentInputName) {
      if (this.uploadingInputs.includes(experimentInputName)) {
        const index = this.uploadingInputs.indexOf(experimentInputName);
        this.uploadingInputs.splice(index, 1);
      }
    },
    inputValueChanged: function () {
      this.localExperiment.evaluateInputDependencies();
    },
    calculateQueueSettings: useDebounceFn(async function () {
      const queueSettingsUpdate =
        await services.QueueSettingsCalculatorService.calculate(
          {
            lookup: this.appInterface.queue_settings_calculator_id,
            data: this.localExperiment,
          },
          { showSpinner: false },
        );
      // Override values in computational_resource_scheduling with the values
      // returned from the queue settings calculator
      Object.assign(
        this.localExperiment.user_configuration_data
          .computational_resource_scheduling,
        queueSettingsUpdate,
      );
    }, 500),
    experimentInputsChanged() {
      if (this.appInterface.queue_settings_calculator_id) {
        this.calculateQueueSettings();
      }
    },
    resourceHostIdChanged() {
      if (this.appInterface.queue_settings_calculator_id) {
        this.calculateQueueSettings();
      }
    },
  },
  watch: {
    experiment: function (newValue) {
      this.localExperiment = newValue.clone();
    },
    localExperiment: {
      handler() {
        this.edited = true;
      },
      deep: true,
    },
    "experiment.experiment_inputs": {
      handler() {
        this.experimentInputsChanged();
      },
      deep: true,
    },
    "experiment.user_configuration_data.computational_resource_scheduling.resource_host_id":
      function () {
        this.resourceHostIdChanged();
      },
  },
};
</script>
