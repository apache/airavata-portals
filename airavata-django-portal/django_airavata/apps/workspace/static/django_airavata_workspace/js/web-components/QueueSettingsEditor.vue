<template>
  <div v-if="showQueueSettings">
    <div class="card border-default">
      <a class="card-link text-dark" @click="showConfiguration = !showConfiguration">
        <div class="card-body">
          <h5 class="card-title mb-4">Settings for queue {{ selectedQueueName }}</h5>
          <div class="row">
            <div class="col">
              <h3 class="h5 mb-0">
                {{ getNodeCount }}
              </h3>
              <span class="text-muted text-uppercase">NODE COUNT</span>
            </div>
            <div class="col">
              <h3 class="h5 mb-0">
                {{ getTotalCPUCount }}
              </h3>
              <span class="text-muted text-uppercase">CORE COUNT</span>
            </div>
            <div class="col">
              <h3 class="h5 mb-0">{{ getWallTimeLimit }} minutes</h3>
              <span class="text-muted text-uppercase">TIME LIMIT</span>
            </div>
            <div v-if="maxMemory > 0" class="col">
              <h3 class="h5 mb-0">{{ getTotalPhysicalMemory }} MB</h3>
              <span class="text-muted text-uppercase">PHYSICAL MEMORY</span>
            </div>
          </div>
        </div>
      </a>
    </div>
    <div v-if="showConfiguration">
      <div class="mb-3" label="Select a Queue" label-for="queue">
        <select
          id="queue"
          class="form-select"
          :value="selectedQueueName"
          required
          @change="queueChanged(($event.target as HTMLInputElement).value)"
          @input.stop
        >
          <option v-for="opt in queueOptions" :key="opt.value" :value="opt.value">
            {{ opt.text }}
          </option>
        </select>
        <div class="form-text text-muted">{{ queueDescription }}</div>
      </div>
      <div class="d-flex flex-row">
        <div class="flex-fill">
          <div class="mb-3" label="Node Count" label-for="node-count">
            <input
              id="node-count"
              class="form-control"
              type="number"
              min="1"
              :max="maxAllowedNodes"
              :value="getNodeCount"
              required
              @input.stop="updateNodeCount"
            />
            <div class="form-text text-muted">
              <i class="fa fa-info-circle" aria-hidden="true"></i>
              Max Allowed Nodes = {{ maxAllowedNodes }}
            </div>
          </div>
          <div class="mb-3" label="Total Core Count" label-for="core-count">
            <input
              id="core-count"
              class="form-control"
              type="number"
              min="1"
              :max="maxAllowedCores"
              :value="getTotalCPUCount"
              required
              @input.stop="updateTotalCPUCount"
            />
            <div class="form-text text-muted">
              <i class="fa fa-info-circle" aria-hidden="true"></i>
              Max Allowed Cores = {{ maxAllowedCores
              }}<template v-if="queue && (queue as any).cpuPerNode > 0"
                >. There are {{ (queue as any).cpuPerNode }} cores per node.
              </template>
            </div>
          </div>
        </div>
        <div v-if="queue && (queue as any).cpuPerNode > 0" class="d-flex flex-column">
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
      <div class="mb-3" label="Wall Time Limit" label-for="walltime-limit">
        <div class="input-group" append="minutes">
          <input
            id="walltime-limit"
            class="form-control"
            type="number"
            min="1"
            :max="maxAllowedWalltime"
            :value="getWallTimeLimit"
            required
            @input.stop="updateWallTimeLimit"
          />
        </div>
        <div class="form-text text-muted">
          <i class="fa fa-info-circle" aria-hidden="true"></i>
          Max Allowed Wall Time = {{ maxAllowedWalltime }} minutes
        </div>
      </div>
      <form-group
        v-if="maxMemory > 0"
        label="Total Physical Memory"
        label-for="total-physical-memory"
      >
        <div class="input-group" append="MB">
          <input
            id="total-physical-memory"
            class="form-control"
            type="number"
            min="0"
            :max="maxMemory"
            :value="getTotalPhysicalMemory"
            @input.stop="updateTotalPhysicalMemory"
          />
        </div>
        <div class="form-text text-muted">
          <i class="fa fa-info-circle" aria-hidden="true"></i>
          Max Physical Memory = {{ maxMemory }} MB
        </div>
      </form-group>
      <div>
        <a class="text-secondary" @click="showConfiguration = false">
          <i class="fa fa-times" aria-hidden="true"></i>
          Hide Settings</a
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, getCurrentInstance } from "vue";
import { utils } from "django-airavata-api";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

// Vue maps kebab-case HTML attribute "total-cpu-count" → camelCase prop "totalCpuCount"
const props = withDefaults(defineProps<{
  queueName?: string;
  nodeCount?: string;
  wallTimeLimit?: string;
  totalPhysicalMemory?: string;
  totalCpuCount?: string;
}>(), {
  queueName: undefined,
  nodeCount: undefined,
  wallTimeLimit: undefined,
  totalPhysicalMemory: undefined,
  totalCpuCount: undefined,
});

const webComponentsStore = useWebComponentsStore();

const showConfiguration = ref(false);
const enableNodeCountToCpuCheck = ref(true);

const queue = computed(() => webComponentsStore.queue);
const queues = computed(() => webComponentsStore.queues as unknown as Array<{ queueName: string; queueDescription?: string }> | null);
const maxAllowedCores = computed(() => webComponentsStore.maxAllowedCores);
const maxAllowedNodes = computed(() => webComponentsStore.maxAllowedNodes);
const maxAllowedWalltime = computed(() => webComponentsStore.maxAllowedWalltime);
const maxMemory = computed(() => webComponentsStore.maxMemory);
const selectedQueueName = computed(() => webComponentsStore.queueName);
const getTotalCPUCount = computed(() => webComponentsStore.totalCPUCount);
const getNodeCount = computed(() => webComponentsStore.nodeCount);
const getWallTimeLimit = computed(() => webComponentsStore.wallTimeLimit);
const getTotalPhysicalMemory = computed(() => webComponentsStore.totalPhysicalMemory);
const showQueueSettings = computed(() => webComponentsStore.showQueueSettings);

const totalCPUCountPropValue = computed(() => props.totalCpuCount);

const queueOptions = computed(() => {
  if (!queues.value) {
    return [];
  }
  const options = queues.value.map((q) => ({
    value: q.queueName,
    text: q.queueName,
  }));
  utils.StringUtils.sortIgnoreCase(options, (q: { text: string }) => q.text);
  return options;
});

const queueDescription = computed(() => {
  const q = queue.value as unknown as { queueDescription?: string } | null;
  return q ? q.queueDescription : null;
});

const currentQueueSettings = computed(() => ({
  queueName: selectedQueueName.value,
  totalCPUCount: getTotalCPUCount.value,
  nodeCount: getNodeCount.value,
  wallTimeLimit: getWallTimeLimit.value,
  totalPhysicalMemory: getTotalPhysicalMemory.value,
}));

function emitValueChanged() {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  if (el) {
    const inputEvent = new CustomEvent("input", {
      detail: [currentQueueSettings.value],
      composed: true,
      bubbles: true,
    });
    el.dispatchEvent(inputEvent);
  }
}

function queueChanged(newQueueName: string) {
  webComponentsStore.updateQueueName({ queueName: newQueueName });
}

function updateNodeCount(event: Event) {
  webComponentsStore.updateNodeCount({
    nodeCount: Number((event.target as HTMLInputElement).value),
    enableNodeCountToCpuCheck: enableNodeCountToCpuCheck.value,
  });
}

function updateTotalCPUCount(event: Event) {
  webComponentsStore.updateTotalCPUCount({
    totalCPUCount: Number((event.target as HTMLInputElement).value),
    enableNodeCountToCpuCheck: enableNodeCountToCpuCheck.value,
  });
}

function updateWallTimeLimit(event: Event) {
  webComponentsStore.updateWallTimeLimit({
    wallTimeLimit: Number((event.target as HTMLInputElement).value),
  });
}

function updateTotalPhysicalMemory(event: Event) {
  webComponentsStore.updateTotalPhysicalMemory({
    totalPhysicalMemory: Number((event.target as HTMLInputElement).value),
  });
}

watch(enableNodeCountToCpuCheck, () => {
  if (enableNodeCountToCpuCheck.value) {
    webComponentsStore.updateNodeCount({
      nodeCount: getNodeCount.value ?? 0,
      enableNodeCountToCpuCheck: enableNodeCountToCpuCheck.value,
    });
  }
});

watch(() => props.queueName, (value) => {
  if (value && selectedQueueName.value !== value) {
    queueChanged(value);
  }
});

watch(() => props.nodeCount, (value) => {
  if (value && getNodeCount.value !== Number(value)) {
    webComponentsStore.updateNodeCount({
      nodeCount: Number(value),
      enableNodeCountToCpuCheck: enableNodeCountToCpuCheck.value,
    });
  }
});

watch(totalCPUCountPropValue, (value) => {
  if (value && getTotalCPUCount.value !== Number(value)) {
    webComponentsStore.updateTotalCPUCount({
      totalCPUCount: Number(value),
      enableNodeCountToCpuCheck: enableNodeCountToCpuCheck.value,
    });
  }
});

watch(() => props.wallTimeLimit, (value) => {
  if (value && getWallTimeLimit.value !== Number(value)) {
    webComponentsStore.updateWallTimeLimit({ wallTimeLimit: Number(value) });
  }
});

watch(() => props.totalPhysicalMemory, (value) => {
  if (value && getTotalPhysicalMemory.value !== Number(value)) {
    webComponentsStore.updateTotalPhysicalMemory({
      totalPhysicalMemory: Number(value),
    });
  }
});

watch(currentQueueSettings, () => {
  emitValueChanged();
});

// Initialize
webComponentsStore.initializeQueueSettings({
  queueName: props.queueName ?? "",
  nodeCount: Number(props.nodeCount ?? 0),
  totalCPUCount: Number(totalCPUCountPropValue.value ?? 0),
  wallTimeLimit: Number(props.wallTimeLimit ?? 0),
  totalPhysicalMemory: Number(props.totalPhysicalMemory ?? 0),
});
</script>

<style lang="scss">
@import "./styles";

:host {
  display: block;
  margin-bottom: 1rem;
}
</style>
