<template>
  <div>
    <div class="row">
      <div class="col">
        <form-group
          label="Compute Resource"
          label-for="compute-resource"
          :feedback="getValidationFeedback('resource_host_id')"
          :state="getValidationState('resource_host_id')"
        >
          <select
            id="compute-resource"
            v-model="resource_host_id"
            class="form-select"
            required
            :state="getValidationState('resource_host_id')"
            :disabled="!computeResourceOptions || computeResourceOptions.length === 0"
            @change="computeResourceChanged(($event.target as HTMLSelectElement).value)"
          >
            <option :value="null" disabled>Select a Compute Resource</option>
            <option v-for="opt in computeResourceOptions" :key="opt.value" :value="opt.value">
              {{ opt.text }}
            </option>
          </select>
        </form-group>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <QueueSettingsEditor
          v-if="appDeploymentId"
          v-model="data"
          :app-module-id="appModuleId"
          :app-deployment-id="appDeploymentId"
          :compute-resource-policy="selectedComputeResourcePolicy"
          :batch-queue-resource-policies="batchQueueResourcePolicies"
          @input="queueSettingsChanged"
          @valid="queueSettingsValidityChanged(true)"
          @invalid="queueSettingsValidityChanged(false)"
        >
        </QueueSettingsEditor>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import QueueSettingsEditor from "./QueueSettingsEditor.vue";
import { errors, models, services, utils as apiUtils } from "django-airavata-api";
import { utils } from "django-airavata-common-ui";

type ComputationalResourceSchedulingModel = InstanceType<typeof models.ComputationalResourceSchedulingModel>;

interface ComputeResourceOption {
  value: string;
  text: string;
}

interface WorkspacePreferences {
  most_recent_compute_resource_id?: string | null;
}

interface GroupResourceProfileData {
  group_resource_profile_id: string;
  compute_resource_policies: Array<{ compute_resource_id: string; [key: string]: unknown }>;
  batch_queue_resource_policies: Array<{ compute_resource_id: string; [key: string]: unknown }>;
}

interface ApplicationDeployment {
  compute_host_id: string;
  app_deployment_id: string;
}

const props = defineProps<{
  modelValue: ComputationalResourceSchedulingModel;
  appModuleId: string;
  groupResourceProfileId: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: ComputationalResourceSchedulingModel];
  input: [value: ComputationalResourceSchedulingModel];
  valid: [];
  invalid: [];
}>();

// VModelMixin inline
function copyValue(value: ComputationalResourceSchedulingModel) {
  return value instanceof models.BaseModel
    ? (value as unknown as { clone: () => ComputationalResourceSchedulingModel }).clone()
    : value;
}

const data = ref<ComputationalResourceSchedulingModel>(copyValue(props.modelValue));

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = copyValue(newValue);
  },
  { deep: true },
);

watch(
  data,
  (newValue, oldValue) => {
    if (typeof props.modelValue === "object" && newValue === oldValue) {
      emit("update:modelValue", newValue);
      emit("input", newValue);
    } else if (
      (props.modelValue === null || typeof props.modelValue !== "object") &&
      newValue !== oldValue
    ) {
      emit("update:modelValue", newValue);
      emit("input", newValue);
    }
  },
  { deep: true },
);

const computeResources = ref<Record<string, string>>({});
const applicationDeployments = ref<ApplicationDeployment[]>([]);
const selectedGroupResourceProfileData = ref<GroupResourceProfileData | null>(null);
const resource_host_id = ref<string | null>(props.modelValue.resource_host_id ?? null);
const invalidQueueSettings = ref(false);
const workspacePreferences = ref<WorkspacePreferences | null>(null);

const localComputationalResourceScheduling = computed(() => data.value);

const computeResourceOptions = computed<ComputeResourceOption[]>(() => {
  const options = applicationDeployments.value.map((dep) => ({
    value: dep.compute_host_id,
    text: dep.compute_host_id in computeResources.value ? computeResources.value[dep.compute_host_id] : "",
  }));
  options.sort((a, b) => a.text.localeCompare(b.text));
  return options;
});

const selectedComputeResourcePolicy = computed(() => {
  if (selectedGroupResourceProfileData.value === null) return null;
  return selectedGroupResourceProfileData.value.compute_resource_policies.find(
    (crp) => crp.compute_resource_id === localComputationalResourceScheduling.value.resource_host_id,
  ) ?? null;
});

interface BatchQueueResourcePolicyLike {
  compute_resource_id: string;
  queuename: string;
  maxAllowedCores: number;
  maxAllowedNodes: number;
  maxAllowedWalltime: number;
  resourcePolicyId?: string;
  [key: string]: unknown;
}

const batchQueueResourcePolicies = computed<BatchQueueResourcePolicyLike[] | null>(() => {
  if (selectedGroupResourceProfileData.value === null) return null;
  return selectedGroupResourceProfileData.value.batch_queue_resource_policies.filter(
    (bqrp) => bqrp.compute_resource_id === localComputationalResourceScheduling.value.resource_host_id,
  ) as BatchQueueResourcePolicyLike[];
});

const appDeploymentId = computed<string | null>(() => {
  if (!resource_host_id.value || applicationDeployments.value.length === 0) return null;
  const selectedDep = applicationDeployments.value.find(
    (dep) => dep.compute_host_id === resource_host_id.value,
  );
  if (!selectedDep) {
    throw new Error("Failed to find application deployment!");
  }
  return selectedDep.app_deployment_id;
});

const validation = computed(() => {
  const queueInfo = {};
  return localComputationalResourceScheduling.value.validate(queueInfo);
});

const valid = computed(() => !invalidQueueSettings.value && Object.keys(validation.value).length === 0);

watch(computeResourceOptions, (newOptions) => {
  if (resource_host_id.value !== null && !newOptions.find((opt) => opt.value === resource_host_id.value)) {
    resource_host_id.value = null;
  }
  if (
    resource_host_id.value === null &&
    workspacePreferences.value?.most_recent_compute_resource_id &&
    newOptions.find((opt) => opt.value === workspacePreferences.value!.most_recent_compute_resource_id)
  ) {
    resource_host_id.value = workspacePreferences.value.most_recent_compute_resource_id;
  }
  if (resource_host_id.value === null && newOptions.length > 0) {
    resource_host_id.value = newOptions[0].value;
  }
  computeResourceChanged(resource_host_id.value);
});

watch(
  () => props.groupResourceProfileId,
  (newGroupResourceProfileId) => {
    loadApplicationDeployments(props.appModuleId, newGroupResourceProfileId);
    if (
      selectedGroupResourceProfileData.value &&
      selectedGroupResourceProfileData.value.group_resource_profile_id !== newGroupResourceProfileId
    ) {
      loadGroupResourceProfile();
    }
  },
);

onMounted(() => {
  loadWorkspacePreferences().then(() => {
    loadApplicationDeployments(props.appModuleId, props.groupResourceProfileId);
  });
  loadComputeResourceNames();
  loadGroupResourceProfile();
  validate();
});

function computeResourceChanged(selectedComputeResourceId: string | null) {
  data.value.resource_host_id = selectedComputeResourceId;
}

function loadApplicationDeployments(appModuleId: string, groupResourceProfileId: string) {
  services.ApplicationDeploymentService.list(
    { app_module_id: appModuleId, group_resource_profile_id: groupResourceProfileId },
    { ignoreErrors: true },
  )
    .then((deps: unknown) => {
      applicationDeployments.value = deps as ApplicationDeployment[];
    })
    .catch((error: unknown) => {
      if (!errors.ErrorUtils.isUnauthorizedError(error)) {
        return Promise.reject(error);
      }
    })
    .catch(apiUtils.FetchUtils.reportError);
}

function loadGroupResourceProfile() {
  services.ProjectResourceProfileService.retrieve(
    { lookup: props.groupResourceProfileId },
    { ignoreErrors: true },
  )
    .then((grp: unknown) => {
      selectedGroupResourceProfileData.value = grp as GroupResourceProfileData;
    })
    .catch((error: unknown) => {
      if (!errors.ErrorUtils.isUnauthorizedError(error)) {
        return Promise.reject(error);
      }
    })
    .catch(apiUtils.FetchUtils.reportError);
}

function loadComputeResourceNames() {
  services.ComputeResourceService.names().then(
    (names: unknown) => (computeResources.value = names as Record<string, string>),
  );
}

function loadWorkspacePreferences(): Promise<void> {
  return services.WorkspacePreferencesService.get().then(
    (prefs: unknown) => (workspacePreferences.value = prefs as WorkspacePreferences),
  );
}

function queueSettingsChanged() {
  localComputationalResourceScheduling.value.resource_host_id = resource_host_id.value;
  emit("input", data.value);
}

function queueSettingsValidityChanged(validValue: boolean) {
  invalidQueueSettings.value = !validValue;
  validate();
}

function validate() {
  if (!valid.value) {
    emit("invalid");
  } else {
    emit("valid");
  }
}

function getValidationFeedback(properties: string): unknown {
  return utils.getProperty(validation.value, properties);
}

function getValidationState(properties: string): boolean | null {
  return getValidationFeedback(properties) ? false : null;
}
</script>

<style></style>
