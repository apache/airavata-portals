<template>
  <div>
    <UnsavedChangesGuard :dirty="dirty" />
    <div class="row">
      <div class="col-auto me-auto">
        <h1 class="h4 mb-4">
          <div v-if="appModule" class="application-name text-muted text-uppercase">
            <i class="fa fa-code" aria-hidden="true"></i>
            {{ appModule.app_module_name }}
          </div>
          <slot name="title">Experiment Editor</slot>
        </h1>
      </div>
      <div class="col-auto">
        <ShareButton
          ref="shareButton"
          :entity-id="localExperiment.experiment_id"
          :entity-label="'Experiment'"
          :parent-entity-id="localExperiment.project_id"
          :parent-entity-label="'Project'"
          :auto-add-default-gateway-users-group="false"
        />
      </div>
    </div>
    <form novalidate>
      <div class="row">
        <div class="col">
          <form-group
            label="Experiment Name"
            label-for="experiment-name"
            :feedback="getValidationFeedback('experiment_name')"
            :state="getValidationState('experiment_name')"
          >
            <input
              id="experiment-name"
              v-model="localExperiment.experiment_name"
              class="form-control"
              type="text"
              required
              placeholder="Experiment name"
              :state="getValidationState('experiment_name')"
            />
          </form-group>
          <ExperimentDescriptionEditor v-model="localExperiment.description" />
        </div>
      </div>
      <div class="row">
        <div class="col">
          <form-group
            label="Project"
            label-for="project"
            :feedback="getValidationFeedback('project_id')"
            :state="getValidationState('project_id')"
          >
            <select
              id="project"
              v-model="localExperiment.project_id"
              class="form-select"
              required
              :state="getValidationState('project_id')"
            >
              <option :value="null" disabled>Select a Project</option>
              <optgroup label="My Projects">
                <option
                  v-for="project in myProjectOptions"
                  :key="project.value"
                  :value="project.value"
                >
                  {{ project.text }}
                </option>
              </optgroup>
              <optgroup label="Projects Shared With Me">
                <option
                  v-for="project in sharedProjectOptions"
                  :key="project.value"
                  :value="project.value"
                >
                  {{ project.text }}
                </option>
              </optgroup>
            </select>
          </form-group>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <WorkspaceNoticesManagementContainer
            v-if="appInterface && (appInterface as Record<string, unknown>).application_description"
            class="mt-2"
            :data="[{ notificationMessage: (appInterface as Record<string, unknown>).application_description as string | undefined }]"
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
                <InputEditorContainer
                  v-for="experimentInput in localExperiment.experiment_inputs"
                  v-show="experimentInput.show"
                  :key="experimentInput.name"
                  v-model="experimentInput.value"
                  :experiment-input="experimentInput"
                  :experiment="localExperiment"
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
      <GroupResourceProfileSelector
        v-model="localExperiment.user_configuration_data.group_resource_profile_id"
        @invalid="invalidGroupResourceProfileSelector = true"
        @valid="invalidGroupResourceProfileSelector = false"
      >
      </GroupResourceProfileSelector>
      <div class="row">
        <div class="col">
          <ComputationalResourceSchedulingEditor
            v-if="localExperiment.user_configuration_data.group_resource_profile_id"
            v-model="localExperiment.user_configuration_data.computational_resource_scheduling"
            :app-module-id="appModule.app_module_id"
            :group-resource-profile-id="
              localExperiment.user_configuration_data.group_resource_profile_id
            "
            @invalid="invalidComputationalResourceSchedulingEditor = true"
            @valid="invalidComputationalResourceSchedulingEditor = false"
          >
          </ComputationalResourceSchedulingEditor>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <div class="mb-3" label="Email Settings">
            <div class="form-check">
              <input
                v-model="localExperiment.enable_email_notification"
                class="form-check-input"
                type="checkbox"
              />
              Receive email notification of experiment status
            </div>
          </div>
        </div>
      </div>
      <div class="row">
        <div id="col-exp-buttons" class="col">
          <button
            class="btn btn-success btn-sm"
            :disabled="isSaveDisabled"
            @click="saveAndLaunchExperiment"
          >
            Save and Launch
          </button>
          <button class="btn btn-primary btn-sm" :disabled="isSaveDisabled" @click="saveExperiment">
            Save
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import ComputationalResourceSchedulingEditor from "./ComputationalResourceSchedulingEditor.vue";
import ExperimentDescriptionEditor from "./ExperimentDescriptionEditor.vue";
import GroupResourceProfileSelector from "./GroupResourceProfileSelector.vue";
import InputEditorContainer from "./input-editors/InputEditorContainer.vue";
import { models, services } from "django-airavata-api";
import { components, utils } from "django-airavata-common-ui";
import WorkspaceNoticesManagementContainer from "../notices/WorkspaceNoticesManagementContainer.vue";

const ShareButton = components.ShareButton;
const UnsavedChangesGuard = components.UnsavedChangesGuard;

type Experiment = InstanceType<typeof models.Experiment>;
type ApplicationModule = InstanceType<typeof models.ApplicationModule>;
type ApplicationInterfaceDefinition = InstanceType<typeof models.ApplicationInterfaceDefinition>;

interface ProjectOption {
  value: string;
  text: string;
}

const props = defineProps<{
  experiment: Experiment;
  appModule: ApplicationModule;
  appInterface: ApplicationInterfaceDefinition;
}>();

const emit = defineEmits<{
  saved: [experiment: Experiment];
  savedAndLaunched: [experiment: Experiment];
}>();

const shareButton = ref<{ mergeAndSave: (_id: string) => Promise<unknown> } | null>(null);

const projects = ref<unknown[]>([]);
const localExperiment = ref<Experiment>(props.experiment.clone() as Experiment);
const invalidInputs = ref<string[]>([]);
const invalidComputationalResourceSchedulingEditor = ref(false);
const invalidGroupResourceProfileSelector = ref(false);
const edited = ref(false);
const saved_ = ref(false);
const uploadingInputs = ref<string[]>([]);

const sharedProjectOptions = computed<ProjectOption[]>(() =>
  (projects.value as Array<Record<string, unknown>>)
    .filter((p) => !p.is_owner)
    .map((project) => ({
      value: project.project_id as string,
      text: project.name + (!project.is_owner ? " (owned by " + project.owner + ")" : ""),
    })),
);

const myProjectOptions = computed<ProjectOption[]>(() =>
  (projects.value as Array<Record<string, unknown>>)
    .filter((p) => p.is_owner)
    .map((project) => ({
      value: project.project_id as string,
      text: project.name as string,
    })),
);

const valid = computed(() => {
  const validation = localExperiment.value.validate();
  return (
    Object.keys(validation).length === 0 &&
    invalidInputs.value.length === 0 &&
    !invalidComputationalResourceSchedulingEditor.value &&
    !invalidGroupResourceProfileSelector.value
  );
});

const isSaveDisabled = computed(() => !valid.value || hasUploadingInputs.value);

const dirty = computed(() => edited.value && !saved_.value);

const hasUploadingInputs = computed(() => uploadingInputs.value.length > 0);

watch(
  () => props.experiment,
  (newValue) => {
    localExperiment.value = newValue.clone() as Experiment;
  },
);

watch(
  localExperiment,
  () => {
    edited.value = true;
  },
  { deep: true },
);

watch(
  () => (props.experiment as unknown as Record<string, unknown>).experiment_inputs,
  () => {
    experimentInputsChanged();
  },
  { deep: true },
);

watch(
  () => {
    const ucd = (props.experiment as unknown as {
      user_configuration_data?: {
        computational_resource_scheduling?: { resource_host_id?: string };
      };
    }).user_configuration_data;
    return ucd?.computational_resource_scheduling?.resource_host_id;
  },
  () => {
    resourceHostIdChanged();
  },
);

onMounted(() => {
  services.ProjectService.listAll().then((projs: unknown) => {
    projects.value = projs as unknown[];
    if (!localExperiment.value.project_id) {
      services.WorkspacePreferencesService.get().then((workspacePreferences: unknown) => {
        const prefs = workspacePreferences as Record<string, unknown>;
        if (!localExperiment.value.project_id) {
          localExperiment.value.project_id = prefs.most_recent_project_id as string;
        }
      });
    }
  });
});

function saveExperiment() {
  return saveOrUpdateExperiment().then((experiment: Experiment) => {
    localExperiment.value = experiment;
    emit("saved", experiment);
  });
}

function saveAndLaunchExperiment() {
  return saveOrUpdateExperiment().then((experiment: Experiment) => {
    localExperiment.value = experiment;
    return services.ExperimentService.launch({
      lookup: experiment.experiment_id,
    }).then(() => {
      emit("savedAndLaunched", experiment);
    });
  });
}

function saveOrUpdateExperiment(): Promise<Experiment> {
  if (localExperiment.value.experiment_id) {
    return services.ExperimentService.update({
      lookup: localExperiment.value.experiment_id,
      data: localExperiment.value,
    }).then((experiment: unknown) => {
      saved_.value = true;
      return experiment as Experiment;
    });
  } else {
    return services.ExperimentService.create({
      data: localExperiment.value,
    }).then((experiment: unknown) => {
      const exp = experiment as Experiment;
      saved_.value = true;
      return shareButton.value!
        .mergeAndSave(exp.experiment_id)
        .then(() => exp);
    });
  }
}

function getValidationFeedback(properties: string): unknown {
  return utils.getProperty(localExperiment.value.validate(), properties);
}

function getValidationState(properties: string): boolean | null {
  return getValidationFeedback(properties) ? false : null;
}

function recordInvalidInputEditorValue(experimentInputName: string) {
  if (!invalidInputs.value.includes(experimentInputName)) {
    invalidInputs.value.push(experimentInputName);
  }
}

function recordValidInputEditorValue(experimentInputName: string) {
  if (invalidInputs.value.includes(experimentInputName)) {
    const index = invalidInputs.value.indexOf(experimentInputName);
    invalidInputs.value.splice(index, 1);
  }
}

function uploadStart(experimentInputName: string) {
  if (!uploadingInputs.value.includes(experimentInputName)) {
    uploadingInputs.value.push(experimentInputName);
  }
}

function uploadEnd(experimentInputName: string) {
  if (uploadingInputs.value.includes(experimentInputName)) {
    const index = uploadingInputs.value.indexOf(experimentInputName);
    uploadingInputs.value.splice(index, 1);
  }
}

function inputValueChanged() {
  (localExperiment.value as unknown as { evaluateInputDependencies: () => void }).evaluateInputDependencies();
}

// Inline debounce wrapper for calculateQueueSettings
let calcTimer: ReturnType<typeof setTimeout> | undefined;
function calculateQueueSettings() {
  clearTimeout(calcTimer);
  calcTimer = setTimeout(async () => {
    const queueSettingsUpdate = await services.QueueSettingsCalculatorService.calculate(
      {
        lookup: (props.appInterface as unknown as Record<string, unknown>).queue_settings_calculator_id,
        data: localExperiment.value,
      },
      { showSpinner: false },
    );
    Object.assign(
      (localExperiment.value as unknown as Record<string, unknown> & { user_configuration_data: Record<string, unknown> }).user_configuration_data.computationalResourceScheduling as object,
      queueSettingsUpdate,
    );
  }, 500);
}

function experimentInputsChanged() {
  if ((props.appInterface as unknown as Record<string, unknown>).queue_settings_calculator_id) {
    calculateQueueSettings();
  }
}

function resourceHostIdChanged() {
  if ((props.appInterface as unknown as Record<string, unknown>).queue_settings_calculator_id) {
    calculateQueueSettings();
  }
}
</script>

<style>
.application-name {
  font-size: 12px;
}

#col-exp-buttons {
  text-align: right;
}
</style>
