<template>
  <div>
    <unsaved-changes-guard :dirty="dirty" />
    <div class="row">
      <div class="col-auto mr-auto">
        <h1 class="h4 mb-4">
          <div
            v-if="appModule"
            class="application-name text-muted text-uppercase"
          >
            <i class="fa fa-code" aria-hidden="true"></i>
            {{ appModule.app_module_name }}
          </div>
          <slot name="title">Experiment Editor</slot>
        </h1>
      </div>
      <div class="col-auto">
        <share-button
          ref="shareButton"
          :entity-id="localExperiment.experiment_id"
          :entity-label="'Experiment'"
          :parent-entity-id="localExperiment.project_id"
          :parent-entity-label="'Project'"
          :auto-add-default-gateway-users-group="false"
        />
      </div>
    </div>
    <b-form novalidate>
      <div class="row">
        <div class="col">
          <b-form-group
            label="Experiment Name"
            label-for="experiment-name"
            :feedback="getValidationFeedback('experiment_name')"
            :state="getValidationState('experiment_name')"
          >
            <b-form-input
              id="experiment-name"
              type="text"
              v-model="localExperiment.experiment_name"
              required
              placeholder="Experiment name"
              :state="getValidationState('experiment_name')"
            ></b-form-input>
          </b-form-group>
          <experiment-description-editor
            v-model="localExperiment.description"
          />
        </div>
      </div>
      <div class="row">
        <div class="col">
          <b-form-group
            label="Project"
            label-for="project"
            :feedback="getValidationFeedback('project_id')"
            :state="getValidationState('project_id')"
          >
            <b-form-select
              id="project"
              v-model="localExperiment.project_id"
              required
              :state="getValidationState('project_id')"
            >
              <template slot="first">
                <option :value="null" disabled>Select a Project</option>
              </template>
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
            </b-form-select>
          </b-form-group>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <workspace-notices-management-container
            class="mt-2"
            v-if="appInterface && appInterface.application_description"
            :data="[
              { notification_message: appInterface.application_description },
            ]"
          />
        </div>
      </div>
      <div class="row">
        <div class="col">
          <h1 class="h4 mt-2 mb-4">Application Configuration</h1>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <div class="card border-default">
            <div class="card-body">
              <h2 class="h6 mb-3">Application Inputs</h2>

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
            </div>
          </div>
        </div>
      </div>
      <group-resource-profile-selector
        v-model="localExperiment.user_configuration_data.group_resource_profile_id"
        @invalid="invalidGroupResourceProfileSelector = true"
        @valid="invalidGroupResourceProfileSelector = false"
      >
      </group-resource-profile-selector>
      <div class="row">
        <div class="col">
          <computational-resource-scheduling-editor
            v-model="
              localExperiment.user_configuration_data
                .computational_resource_scheduling
            "
            v-if="localExperiment.user_configuration_data.group_resource_profile_id"
            :app-module-id="appModule.app_module_id"
            :group-resource-profile-id="
              localExperiment.user_configuration_data.group_resource_profile_id
            "
            @invalid="invalidComputationalResourceSchedulingEditor = true"
            @valid="invalidComputationalResourceSchedulingEditor = false"
          >
          </computational-resource-scheduling-editor>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <b-form-group label="Email Settings">
            <b-form-checkbox v-model="localExperiment.enable_email_notification">
              Receive email notification of experiment status
            </b-form-checkbox>
          </b-form-group>
        </div>
      </div>
      <div class="row">
        <div id="col-exp-buttons" class="col">
          <b-button
            variant="success"
            @click="saveAndLaunchExperiment"
            :disabled="isSaveDisabled"
          >
            Save and Launch
          </b-button>
          <b-button
            variant="primary"
            @click="saveExperiment"
            :disabled="isSaveDisabled"
          >
            Save
          </b-button>
        </div>
      </div>
    </b-form>
  </div>
</template>

<script>
import ComputationalResourceSchedulingEditor from "./ComputationalResourceSchedulingEditor.vue";
import ExperimentDescriptionEditor from "./ExperimentDescriptionEditor.vue";
import GroupResourceProfileSelector from "./GroupResourceProfileSelector.vue";
import InputEditorContainer from "./input-editors/InputEditorContainer.vue";
import { models, services } from "django-airavata-api";
import { components, utils } from "django-airavata-common-ui";
import WorkspaceNoticesManagementContainer from "../notices/WorkspaceNoticesManagementContainer";
import _ from "lodash";

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
    WorkspaceNoticesManagementContainer,
    ComputationalResourceSchedulingEditor,
    ExperimentDescriptionEditor,
    GroupResourceProfileSelector,
    InputEditorContainer,
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
          }
        );
      }
    });
  },
  computed: {
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
    calculateQueueSettings: _.debounce(async function () {
      const queueSettingsUpdate = await services.QueueSettingsCalculatorService.calculate(
        {
          lookup: this.appInterface.queue_settings_calculator_id,
          data: this.localExperiment,
        },
        { showSpinner: false }
      );
      // Override values in computational_resource_scheduling with the values
      // returned from the queue settings calculator
      Object.assign(
        this.localExperiment.user_configuration_data
          .computational_resource_scheduling,
        queueSettingsUpdate
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
    "experiment.user_configuration_data.computational_resource_scheduling.resource_host_id": function () {
      this.resourceHostIdChanged();
    },
  },
};
</script>

<style>
.application-name {
  font-size: 12px;
}

#col-exp-buttons {
  text-align: right;
}
</style>
