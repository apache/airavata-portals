<template>
  <div v-if="showQueueSettings">
    <div class="row">
      <div class="col">
        <div :class="['card border-default', { 'border-danger': !valid, 'is-disabled': disabled }]">
          <a
            class="card-link text-dark"
            :disabled="disabled"
            @click="showConfiguration = !showConfiguration"
          >
            <div class="card-body">
              <h5 class="card-title mb-4">Settings for queue {{ data.queue_name }}</h5>
              <div class="row">
                <div class="col">
                  <h3 class="h5 mb-0">
                    {{ data.node_count }}
                  </h3>
                  <span class="text-muted text-uppercase">NODE COUNT</span>
                </div>
                <div class="col">
                  <h3 class="h5 mb-0">
                    {{ data.total_cpu_count }}
                  </h3>
                  <span class="text-muted text-uppercase">CORE COUNT</span>
                </div>
                <div class="col">
                  <h3 class="h5 mb-0">{{ data.wall_time_limit }} minutes</h3>
                  <span class="text-muted text-uppercase">TIME LIMIT</span>
                </div>
                <div v-if="maxPhysicalMemory > 0" class="col">
                  <h3 class="h5 mb-0">{{ data.total_physical_memory }} MB</h3>
                  <span class="text-muted text-uppercase">PHYSICAL MEMORY</span>
                </div>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
    <div v-if="showConfiguration">
      <div class="row">
        <div class="col">
          <form-group
            label="Select a Queue"
            label-for="queue"
            :invalid-feedback="getValidationFeedback('queue_name')"
            :state="getValidationState('queue_name')"
          >
            <select
              id="queue"
              v-model="data.queue_name"
              class="form-select"
              required
              @change="queueChanged"
            >
              <option v-for="opt in queueOptions" :key="opt.value" :value="opt.value">
                {{ opt.text }}
              </option>
            </select>
            <small class="form-text text-muted">{{ queueDescription }}</small>
          </form-group>
        </div>
        <div class="d-flex flex-row">
          <div class="flex-fill">
            <form-group
              label="Node Count"
              label-for="node-count"
              :invalid-feedback="getValidationFeedback('nodeCount')"
              :state="getValidationState('nodeCount', true)"
            >
              <input
                id="node-count"
                v-model="data.node_count"
                class="form-control"
                type="number"
                min="1"
                :max="maxNodes"
                required
                @input="nodeCountChanged"
              />
              <small class="form-text text-muted">
                <i class="fa fa-info-circle" aria-hidden="true"></i>
                Max Allowed Nodes = {{ maxNodes }}
              </small>
            </form-group>
          </div>
          <div class="flex-fill">
            <form-group
              label="Total Core Count"
              label-for="core-count"
              :invalid-feedback="getValidationFeedback('totalCPUCount')"
              :state="getValidationState('totalCPUCount', true)"
            >
              <input
                id="core-count"
                v-model="data.total_cpu_count"
                class="form-control"
                type="number"
                min="1"
                :max="maxCPUCount"
                required
                @input="cpuCountChanged"
              />
              <small class="form-text text-muted">
                <i class="fa fa-info-circle" aria-hidden="true"></i>
                Max Allowed Cores = {{ maxCPUCount
                }}<template v-if="selectedQueueDefault && selectedQueueDefault.cpu_per_node > 0"
                  >. There are {{ selectedQueueDefault.cpu_per_node }} cores per node.
                </template>
              </small>
            </form-group>
          </div>
        </div>
        <div
          v-if="selectedQueueDefault && selectedQueueDefault.cpu_per_node > 0"
          class="d-flex flex-column"
        >
          <div
            class="flex-fill"
            style="
              border: 1px solid #6c757d;
              border-top-right-radius: 10px;
              margin-top: 51px;
              border-left-width: 0px;
              border-bottom-width: 0px;
              margin-right: 15px;
            "
          ></div>
          <button
            class="btn btn-sm btn-outline-secondary rounded-pill"
            @click="enableNodeCountToCpuCheck = !enableNodeCountToCpuCheck"
          >
            <i v-if="enableNodeCountToCpuCheck" class="fa fa-lock" aria-hidden="true"></i>
            <i v-else class="fa fa-unlock" aria-hidden="true"></i>
          </button>
          <div
            class="flex-fill"
            style="
              border: 1px solid #6c757d;
              border-bottom-right-radius: 10px;
              margin-bottom: 57px;
              border-left-width: 0px;
              border-top-width: 0px;
              margin-right: 15px;
            "
          ></div>
        </div>
      </div>
      <form-group
        label="Wall Time Limit"
        label-for="walltime-limit"
        :invalid-feedback="getValidationFeedback('wallTimeLimit')"
        :state="getValidationState('wallTimeLimit', true)"
      >
        <div class="input-group">
          <input
            id="walltime-limit"
            v-model="data.wall_time_limit"
            class="form-control"
            type="number"
            min="1"
            :max="maxWalltime"
            required
          />
          <span class="input-group-text">minutes</span>
        </div>
        <small class="form-text text-muted">
          <i class="fa fa-info-circle" aria-hidden="true"></i>
          Max Allowed Wall Time = {{ maxWalltime }} minutes
        </small>
      </form-group>
      <form-group
        v-if="maxPhysicalMemory > 0"
        label="Total Physical Memory"
        label-for="total-physical-memory"
        :invalid-feedback="getValidationFeedback('totalPhysicalMemory')"
        :state="getValidationState('totalPhysicalMemory', true)"
      >
        <div class="input-group">
          <input
            id="total-physical-memory"
            v-model="data.total_physical_memory"
            class="form-control"
            type="number"
            min="0"
            :max="maxPhysicalMemory"
          />
          <span class="input-group-text">MB</span>
        </div>
        <small class="form-text text-muted">
          <i class="fa fa-info-circle" aria-hidden="true"></i>
          Max Physical Memory = {{ maxPhysicalMemory }} MB
        </small>
      </form-group>
      <div>
        <a class="text-secondary action-link" href="#" @click.prevent="showConfiguration = false">
          <i class="fa fa-times text-secondary" aria-hidden="true"></i>
          Hide Settings</a
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models, services } from "django-airavata-api";
import { utils } from "django-airavata-common-ui";

type ComputationalResourceSchedulingModel = InstanceType<typeof models.ComputationalResourceSchedulingModel>;
type ComputeResourcePolicy = InstanceType<typeof models.ComputeResourcePolicy>;

interface QueueDefault {
  queue_name: string;
  queue_description?: string;
  max_processors: number;
  max_nodes: number;
  max_run_time: number;
  max_memory: number;
  default_cpu_count: number;
  default_node_count: number;
  default_walltime: number;
  is_default_queue: boolean;
  cpu_per_node: number;
}

interface BatchQueueResourcePolicy {
  queuename: string;
  maxAllowedCores: number;
  maxAllowedNodes: number;
  maxAllowedWalltime: number;
  resourcePolicyId?: string;
}

interface ApplicationInterface {
  show_queue_settings: boolean;
  queue_settings_calculator_id?: string;
}

const props = defineProps<{
  modelValue: ComputationalResourceSchedulingModel;
  appDeploymentId: string;
  appModuleId: string;
  computeResourcePolicy?: ComputeResourcePolicy | null;
  batchQueueResourcePolicies?: BatchQueueResourcePolicy[] | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: ComputationalResourceSchedulingModel];
  valid: [];
  invalid: [];
  input: [value: ComputationalResourceSchedulingModel];
}>();

// VModelMixin inline
function copyValue(value: ComputationalResourceSchedulingModel) {
  return value instanceof models.BaseModel ? (value as unknown as { clone: () => ComputationalResourceSchedulingModel }).clone() : value;
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

const showConfiguration = ref(false);
const appDeploymentQueues = ref<QueueDefault[] | null>(null);
const enableNodeCountToCpuCheck = ref(true);
const applicationInterface = ref<ApplicationInterface | null>(null);

const queueOptions = computed(() =>
  queueDefaults.value.map((queueDefault) => ({
    value: queueDefault.queue_name,
    text: queueDefault.queue_name,
  })),
);

const selectedQueueDefault = computed<QueueDefault | undefined>(() =>
  queueDefaults.value.find((queue) => queue.queue_name === data.value.queue_name),
);

const batchQueueResourcePolicyComputed = computed<BatchQueueResourcePolicy | null>(() => {
  if (!selectedQueueDefault.value) return null;
  return getBatchQueueResourcePolicy(selectedQueueDefault.value.queue_name);
});

const maxCPUCount = computed<number>(() => {
  if (!selectedQueueDefault.value) return 0;
  const bqrp = batchQueueResourcePolicyComputed.value;
  if (bqrp) {
    return Math.min(bqrp.maxAllowedCores, selectedQueueDefault.value.max_processors);
  }
  return selectedQueueDefault.value.max_processors;
});

const maxNodes = computed<number>(() => {
  if (!selectedQueueDefault.value) return 0;
  const bqrp = batchQueueResourcePolicyComputed.value;
  if (bqrp) {
    return Math.min(bqrp.maxAllowedNodes, selectedQueueDefault.value.max_nodes);
  }
  return selectedQueueDefault.value.max_nodes;
});

const maxWalltime = computed<number>(() => {
  if (!selectedQueueDefault.value) return 0;
  const bqrp = batchQueueResourcePolicyComputed.value;
  if (bqrp) {
    return Math.min(bqrp.maxAllowedWalltime, selectedQueueDefault.value.max_run_time);
  }
  return selectedQueueDefault.value.max_run_time;
});

const maxPhysicalMemory = computed<number>(() =>
  selectedQueueDefault.value ? selectedQueueDefault.value.max_memory : 0,
);

const queueDefaults = computed<QueueDefault[]>(() => {
  if (!appDeploymentQueues.value) return [];
  return appDeploymentQueues.value
    .filter((q) => isQueueInComputeResourcePolicy(q.queue_name))
    .sort((a, b) => {
      if (a.is_default_queue) return -1;
      if (b.is_default_queue) return 1;
      return a.queue_name.localeCompare(b.queue_name);
    });
});

const validation = computed(() => {
  if (!selectedQueueDefault.value) {
    return data.value.validate();
  }
  return data.value.validate(selectedQueueDefault.value, batchQueueResourcePolicyComputed.value);
});

const valid = computed(() => Object.keys(validation.value).length === 0);

const showQueueSettings = computed<boolean>(() =>
  applicationInterface.value ? applicationInterface.value.show_queue_settings : false,
);

const disabled = computed<boolean>(
  () => !!(applicationInterface.value && applicationInterface.value.queue_settings_calculator_id),
);

const queueDescription = computed<string | null>(() =>
  selectedQueueDefault.value ? (selectedQueueDefault.value.queue_description ?? null) : null,
);

watch(enableNodeCountToCpuCheck, () => {
  if (enableNodeCountToCpuCheck.value) {
    nodeCountChanged();
  }
});

watch(
  () => props.appDeploymentId,
  () => {
    loadAppDeploymentQueues().then(() => setDefaultQueue());
  },
);

watch(batchQueueResourcePolicyComputed, (value, oldValue) => {
  if (value && (!oldValue || value.resourcePolicyId !== oldValue.resourcePolicyId)) {
    applyBatchQueueResourcePolicy();
  }
});

watch(
  () => props.computeResourcePolicy,
  () => {
    if (!isQueueInComputeResourcePolicy(data.value.queue_name)) {
      setDefaultQueue();
    }
  },
);

watch(
  () => props.modelValue,
  () => {
    validate();
  },
  { deep: true },
);

onMounted(() => {
  loadAppDeploymentQueues().then(() => {
    if (!props.modelValue.queue_name) {
      setDefaultQueue();
    }
  });
  validate();
  loadApplicationInterface();
});

function queueChanged(event: Event) {
  const queueName = (event.target as HTMLSelectElement).value;
  const queueDefault = queueDefaults.value.find((queue) => queue.queue_name === queueName);
  if (queueDefault) {
    data.value.total_cpu_count = getDefaultCPUCount(queueDefault);
    data.value.node_count = getDefaultNodeCount(queueDefault);
    data.value.wall_time_limit = getDefaultWalltime(queueDefault);
    if (maxPhysicalMemory.value === 0) {
      data.value.total_physical_memory = 0;
    }
  }
}

function validate() {
  if (!valid.value) {
    emit("invalid");
  } else {
    emit("valid");
  }
}

function loadAppDeploymentQueues(): Promise<void> {
  return services.ApplicationDeploymentService.getQueues({
    lookup: props.appDeploymentId,
  }).then((queueDefaults: unknown) => {
    appDeploymentQueues.value = queueDefaults as QueueDefault[];
  });
}

function setDefaultQueue() {
  if (queueDefaults.value.length === 0) {
    data.value.queue_name = null;
    return;
  }
  const defaultQueue = queueDefaults.value[0];
  data.value.queue_name = defaultQueue.queue_name;
  data.value.total_cpu_count = getDefaultCPUCount(defaultQueue);
  data.value.node_count = getDefaultNodeCount(defaultQueue);
  data.value.wall_time_limit = getDefaultWalltime(defaultQueue);
  if (maxPhysicalMemory.value === 0) {
    data.value.total_physical_memory = 0;
  }
}

function isQueueInComputeResourcePolicy(queue_name: string): boolean {
  if (!props.computeResourcePolicy) return true;
  return (props.computeResourcePolicy as unknown as { allowedBatchQueues: string[] }).allowedBatchQueues.includes(queue_name);
}

function getBatchQueueResourcePolicy(queueName: string): BatchQueueResourcePolicy | null {
  if (!props.batchQueueResourcePolicies || props.batchQueueResourcePolicies.length === 0) {
    return null;
  }
  return props.batchQueueResourcePolicies.find((bqrp) => bqrp.queuename === queueName) ?? null;
}

function getDefaultCPUCount(queueDefault: QueueDefault): number {
  const bqrp = batchQueueResourcePolicyComputed.value;
  if (bqrp) {
    return Math.min(bqrp.maxAllowedCores, queueDefault.default_cpu_count);
  }
  return queueDefault.default_cpu_count;
}

function getDefaultNodeCount(queueDefault: QueueDefault): number {
  const bqrp = batchQueueResourcePolicyComputed.value;
  if (bqrp) {
    return Math.min(bqrp.maxAllowedNodes, queueDefault.default_node_count);
  }
  return queueDefault.default_node_count;
}

function getDefaultWalltime(queueDefault: QueueDefault): number {
  const bqrp = batchQueueResourcePolicyComputed.value;
  if (bqrp) {
    return Math.min(bqrp.maxAllowedWalltime, queueDefault.default_walltime);
  }
  return queueDefault.default_walltime;
}

function getValidationFeedback(properties: string): unknown {
  return utils.getProperty(validation.value, properties);
}

function getValidationState(properties: string, showValidState?: boolean): boolean | null {
  return getValidationFeedback(properties) ? false : showValidState ? true : null;
}

function applyBatchQueueResourcePolicy() {
  if (selectedQueueDefault.value) {
    data.value.total_cpu_count = Math.min(data.value.total_cpu_count, maxCPUCount.value);
    data.value.node_count = Math.min(data.value.node_count, maxNodes.value);
    data.value.wall_time_limit = Math.min(data.value.wall_time_limit, maxWalltime.value);
  }
}

function nodeCountChanged() {
  if (enableNodeCountToCpuCheck.value && selectedQueueDefault.value && selectedQueueDefault.value.cpu_per_node > 0) {
    const nodeCount = parseInt(String(data.value.node_count));
    data.value.total_cpu_count = Math.min(
      nodeCount * selectedQueueDefault.value.cpu_per_node,
      maxCPUCount.value,
    );
  }
}

function cpuCountChanged() {
  if (enableNodeCountToCpuCheck.value && selectedQueueDefault.value && selectedQueueDefault.value.cpu_per_node > 0) {
    const cpuCount = parseInt(String(data.value.total_cpu_count));
    if (cpuCount > 0) {
      data.value.node_count = Math.min(
        Math.ceil(cpuCount / selectedQueueDefault.value.cpu_per_node),
        maxNodes.value,
      );
    }
  }
}

function loadApplicationInterface() {
  services.ApplicationModuleService.getApplicationInterface({
    lookup: props.appModuleId,
  }).then((iface: unknown) => {
    applicationInterface.value = iface as ApplicationInterface;
  });
}
</script>

<style></style>
