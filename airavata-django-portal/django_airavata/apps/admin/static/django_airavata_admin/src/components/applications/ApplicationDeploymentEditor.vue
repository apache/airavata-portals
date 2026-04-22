<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-1">
          {{ name }}
        </h1>
        <p v-if="owner" class="mb-2 text-muted">
          Created by <span :title="ownerTitle ?? ''">{{ ownerUserId }}</span>
        </p>
        <share-button
          v-if="localSharedEntity"
          class="mt-2 mb-2"
          :shared-entity="localSharedEntity"
          @saved="savedSharedEntity"
          @unsaved="unsavedSharedEntity"
        />
        <form-group label="Application Executable Path" label-for="executable-path">
          <input
            id="executable-path"
            v-model="data.executablePath"
            class="form-control"
            type="text"
            required
            :disabled="readonly"
          />
        </form-group>
        <form-group label="Application Parallelism Type" label-for="parallelism-type">
          <select
            id="parallelism-type"
            v-model="data.parallelism"
            class="form-select"
            :options="parallelismTypeOptions"
            :disabled="readonly"
          />
        </form-group>
        <form-group label="Application Deployment Description" label-for="deployment-description">
          <textarea
            id="deployment-description"
            v-model="data.appDeploymentDescription"
            class="form-control"
            :rows="3"
            :disabled="readonly"
          ></textarea>
        </form-group>
        <command-objects-editor
          v-model="data.moduleLoadCmds"
          title="Module Load Commands"
          add-button-label="Add Module Load Command"
          :readonly="readonly"
        />
        <set-env-paths-editor
          v-model="data.libPrependPaths"
          title="Library Prepend Paths"
          add-button-label="Add a Library Prepend Path"
          :readonly="readonly"
        />
        <set-env-paths-editor
          v-model="data.libAppendPaths"
          title="Library Append Paths"
          add-button-label="Add a Library Append Path"
          :readonly="readonly"
        />
        <set-env-paths-editor
          v-model="data.setEnvironment"
          title="Environment Variables"
          add-button-label="Add Environment Variable"
          :readonly="readonly"
        />
        <command-objects-editor
          v-model="data.preJobCommands"
          title="Pre Job Commands"
          add-button-label="Add Pre Job Command"
          :readonly="readonly"
        />
        <command-objects-editor
          v-model="data.postJobCommands"
          title="Post Job Commands"
          add-button-label="Add Post Job Command"
          :readonly="readonly"
        />
        <div class="mb-3" label="Default Queue Name" label-for="default-queue-name">
          <select
            id="default-queue-name"
            v-model="data.defaultQueueName"
            class="form-select"
            :disabled="readonly"
            @change="defaultQueueChanged"
          >
            <option :value="null">Select a Default Queue</option>
            <option v-for="opt in queueNameOptions" :key="opt.value" :value="opt.value">
              {{ opt.text }}
            </option>
          </select>
        </div>
        <div class="mb-3" label="Default Node Count" label-for="default-node-count">
          <input
            id="default-node-count"
            v-model="data.defaultNodeCount"
            class="form-control"
            type="number"
            min="0"
            :max="maxNodes"
            :disabled="defaultQueueAttributesDisabled"
          />
        </div>
        <div class="mb-3" label="Default CPU Count" label-for="default-cpu-count">
          <input
            id="default-cpu-count"
            v-model="data.defaultCPUCount"
            class="form-control"
            type="number"
            min="0"
            :max="maxCPUCount"
            :disabled="defaultQueueAttributesDisabled"
          />
          <small v-if="cpuPerNode > 0" class="form-text text-muted">
            There are {{ cpuPerNode }} cores per node.
          </small>
        </div>
        <form-group label="Default Walltime (in minutes)" label-for="default-walltime">
          <input
            id="default-walltime"
            v-model="data.defaultWalltime"
            class="form-control"
            type="number"
            min="0"
            :max="maxWalltime"
            :disabled="defaultQueueAttributesDisabled"
          />
        </form-group>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models, services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import CommandObjectsEditor from "./CommandObjectsEditor.vue";
import SetEnvPathsEditor from "./SetEnvPathsEditor.vue";

const ShareButton = components.ShareButton;

type AppDeployment = InstanceType<typeof models.ApplicationDeploymentDescription>;
type SharedEntity = InstanceType<typeof models.SharedEntity>;

interface BatchQueue {
  queue_name: string;
  max_nodes: number;
  max_processors: number;
  max_run_time: number;
  cpu_per_node: number;
  default_node_count: number;
  default_cpu_count: number;
  default_walltime: number;
}

interface ComputeResource {
  host_name: string;
  batch_queues: BatchQueue[];
}

const props = defineProps<{
  modelValue: AppDeployment;
  readonly?: boolean;
  sharedEntity: SharedEntity;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: AppDeployment];
  "sharing-changed": [sharedEntity: SharedEntity, data: AppDeployment, dirty: boolean];
}>();

const computeResource = ref<ComputeResource | null>(null);
const localSharedEntity = ref<SharedEntity | null>(
  props.sharedEntity ? (props.sharedEntity.clone() as SharedEntity) : null,
);
const dirty = ref(false);

const data = ref<AppDeployment>(
  props.modelValue.clone() as AppDeployment,
);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue.clone() as AppDeployment;
    dirty.value = true;
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

watch(
  () => props.sharedEntity,
  (newValue) => {
    localSharedEntity.value = newValue.clone() as SharedEntity;
  },
);

onMounted(() => {
  services.ComputeResourceService.retrieve({
    lookup: (data.value as { computeHostId: string }).computeHostId,
  }).then((cr: unknown) => {
    computeResource.value = cr as ComputeResource;
  });
});

const name = computed(() => {
  if (computeResource.value) {
    return computeResource.value.host_name;
  } else {
    return String((data.value as { computeHostId: string }).computeHostId).substring(0, 10) + "...";
  }
});

const parallelismTypeOptions = computed(() =>
  (models.ParallelismType.values as Array<{ name: string }>).map((parType) => ({
    value: parType,
    text: parType.name,
  })),
);

const queueNameOptions = computed(() => {
  if (!computeResource.value) {
    return [];
  }
  return computeResource.value.batch_queues.map((queue) => ({
    value: queue.queue_name,
    text: queue.queue_name,
  }));
});

function findQueue(): BatchQueue | null {
  if (!computeResource.value) return null;
  return computeResource.value.batch_queues.find(
    (q) => q.queue_name === (data.value as { defaultQueueName: string }).defaultQueueName,
  ) ?? null;
}

const maxNodes = computed(() => findQueue()?.max_nodes ?? 0);
const maxCPUCount = computed(() => findQueue()?.max_processors ?? 0);
const maxWalltime = computed(() => findQueue()?.max_run_time ?? 0);
const cpuPerNode = computed(() => findQueue()?.cpu_per_node ?? 0);

const defaultQueueAttributesDisabled = computed(
  () => !(data.value as { defaultQueueName?: string | null }).defaultQueueName || props.readonly,
);

const owner = computed(() =>
  localSharedEntity.value && (localSharedEntity.value as { owner?: unknown }).owner
    ? (localSharedEntity.value as { owner: Record<string, string> }).owner
    : null,
);

const ownerUserId = computed(() => owner.value?.user_id ?? null);

const ownerTitle = computed(() =>
  owner.value
    ? owner.value.first_name + " " + owner.value.last_name + " (" + owner.value.email + ")"
    : null,
);

function defaultQueueChanged(event: Event) {
  const queueName = (event.target as HTMLSelectElement).value;
  const dep = data.value as {
    defaultNodeCount: number | null;
    defaultCPUCount: number | null;
    defaultWalltime: number | null;
  };
  if (queueName) {
    const queue = computeResource.value?.batch_queues.find((q) => q.queue_name === queueName);
    if (queue) {
      dep.defaultNodeCount = queue.default_node_count;
      dep.defaultCPUCount = queue.default_cpu_count;
      dep.defaultWalltime = queue.default_walltime;
    }
  } else {
    dep.defaultNodeCount = null;
    dep.defaultCPUCount = null;
    dep.defaultWalltime = null;
  }
}

function savedSharedEntity(newSharedEntity: SharedEntity) {
  emit("sharing-changed", newSharedEntity, data.value, false);
}

function unsavedSharedEntity(newSharedEntity: SharedEntity) {
  dirty.value = true;
  emit("sharing-changed", newSharedEntity, data.value, true);
}
</script>
