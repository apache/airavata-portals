<template>
  <div v-if="showQueueSettings">
    <div>
      <Card :class="{ 'border-destructive': !valid, 'opacity-50': disabled }">
        <a
          href="#"
          class="block text-foreground"
          :class="{ 'pointer-events-none': disabled }"
          @click.prevent="disabled || (showConfiguration = !showConfiguration)"
        >
          <CardContent>
            <h5 class="mb-4 text-lg font-semibold">
              Settings for queue {{ data.queue_name }}
            </h5>
            <div class="flex flex-wrap gap-4">
              <div class="flex-1">
                <h3 class="mb-0 text-lg font-semibold">
                  {{ data.node_count }}
                </h3>
                <span class="text-muted-foreground uppercase">NODE COUNT</span>
              </div>
              <div class="flex-1">
                <h3 class="mb-0 text-lg font-semibold">
                  {{ data.total_cpu_count }}
                </h3>
                <span class="text-muted-foreground uppercase">CORE COUNT</span>
              </div>
              <div class="flex-1">
                <h3 class="mb-0 text-lg font-semibold">
                  {{ data.wall_time_limit }} minutes
                </h3>
                <span class="text-muted-foreground uppercase">TIME LIMIT</span>
              </div>
              <div class="flex-1" v-if="maxPhysicalMemory > 0">
                <h3 class="mb-0 text-lg font-semibold">
                  {{ data.total_physical_memory }} MB
                </h3>
                <span class="text-muted-foreground uppercase"
                  >PHYSICAL MEMORY</span
                >
              </div>
            </div>
          </CardContent>
        </a>
      </Card>
    </div>
    <div v-if="showConfiguration" class="mt-4">
      <div>
        <div class="space-y-1.5">
          <Label for="queue">Select a Queue</Label>
          <select
            id="queue"
            v-model="data.queue_name"
            required
            :aria-invalid="getValidationState('queueName') === false"
            :class="nativeSelectClass"
            @change="queueChanged"
          >
            <option
              v-for="option in queueOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.text }}
            </option>
          </select>
          <p
            v-if="getValidationState('queueName') === false"
            class="text-sm text-destructive"
          >
            {{ getValidationFeedback("queueName") }}
          </p>
          <p class="text-sm text-muted-foreground">
            {{ queueDescription }}
          </p>
        </div>
        <div class="mt-4 flex flex-row">
          <div class="flex-1">
            <div class="space-y-1.5">
              <Label for="node-count">Node Count</Label>
              <Input
                id="node-count"
                type="number"
                min="1"
                :max="maxNodes"
                v-model="data.node_count"
                required
                :aria-invalid="getValidationState('nodeCount', true) === false"
                @update:model-value="nodeCountChanged"
              />
              <p
                v-if="getValidationState('nodeCount', true) === false"
                class="text-sm text-destructive"
              >
                {{ getValidationFeedback("nodeCount") }}
              </p>
              <p class="text-sm text-muted-foreground">
                <Info class="inline size-4" aria-hidden="true" />
                Max Allowed Nodes = {{ maxNodes }}
              </p>
            </div>
            <div class="mt-4 space-y-1.5">
              <Label for="core-count">Total Core Count</Label>
              <Input
                id="core-count"
                type="number"
                min="1"
                :max="maxCPUCount"
                v-model="data.total_cpu_count"
                required
                :aria-invalid="
                  getValidationState('totalCPUCount', true) === false
                "
                @update:model-value="cpuCountChanged"
              />
              <p
                v-if="getValidationState('totalCPUCount', true) === false"
                class="text-sm text-destructive"
              >
                {{ getValidationFeedback("totalCPUCount") }}
              </p>
              <p class="text-sm text-muted-foreground">
                <Info class="inline size-4" aria-hidden="true" />
                Max Allowed Cores = {{ maxCPUCount
                }}<template
                  v-if="
                    selectedQueueDefault &&
                    selectedQueueDefault.cpu_per_node > 0
                  "
                  >. There are {{ selectedQueueDefault.cpu_per_node }} cores per
                  node.
                </template>
              </p>
            </div>
          </div>
          <div
            class="flex flex-col"
            v-if="selectedQueueDefault && selectedQueueDefault.cpu_per_node > 0"
          >
            <div
              class="flex-1"
              style="
                border: 1px solid #6c757d;
                border-top-right-radius: 10px;
                margin-top: 51px;
                border-left-width: 0px;
                border-bottom-width: 0px;
                margin-right: 15px;
              "
            ></div>
            <Button
              size="icon-sm"
              variant="outline"
              class="rounded-full"
              v-on:click="
                enableNodeCountToCpuCheck = !enableNodeCountToCpuCheck
              "
            >
              <Lock
                v-if="enableNodeCountToCpuCheck"
                class="size-4"
                aria-hidden="true"
              />
              <LockOpen v-else class="size-4" aria-hidden="true" />
            </Button>
            <div
              class="flex-1"
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
        <div class="mt-4 space-y-1.5">
          <Label for="walltime-limit">Wall Time Limit</Label>
          <div class="flex">
            <Input
              id="walltime-limit"
              class="rounded-r-none"
              type="number"
              min="1"
              :max="maxWalltime"
              v-model="data.wall_time_limit"
              required
              :aria-invalid="
                getValidationState('wallTimeLimit', true) === false
              "
            />
            <span
              class="flex items-center rounded-r-md border border-l-0 border-input px-3 text-sm text-muted-foreground"
              >minutes</span
            >
          </div>
          <p
            v-if="getValidationState('wallTimeLimit', true) === false"
            class="text-sm text-destructive"
          >
            {{ getValidationFeedback("wallTimeLimit") }}
          </p>
          <p class="text-sm text-muted-foreground">
            <Info class="inline size-4" aria-hidden="true" />
            Max Allowed Wall Time = {{ maxWalltime }} minutes
          </p>
        </div>
        <div class="mt-4 space-y-1.5" v-if="maxPhysicalMemory > 0">
          <Label for="total-physical-memory">Total Physical Memory</Label>
          <div class="flex">
            <Input
              id="total-physical-memory"
              class="rounded-r-none"
              type="number"
              min="0"
              :max="maxPhysicalMemory"
              v-model="data.total_physical_memory"
              :aria-invalid="
                getValidationState('totalPhysicalMemory', true) === false
              "
            />
            <span
              class="flex items-center rounded-r-md border border-l-0 border-input px-3 text-sm text-muted-foreground"
              >MB</span
            >
          </div>
          <p
            v-if="getValidationState('totalPhysicalMemory', true) === false"
            class="text-sm text-destructive"
          >
            {{ getValidationFeedback("totalPhysicalMemory") }}
          </p>
          <p class="text-sm text-muted-foreground">
            <Info class="inline size-4" aria-hidden="true" />
            Max Physical Memory = {{ maxPhysicalMemory }} MB
          </p>
        </div>
        <div class="mt-4">
          <a
            class="inline-flex items-center gap-1 text-muted-foreground"
            href="#"
            @click.prevent="showConfiguration = false"
          >
            <X class="size-4" aria-hidden="true" />
            Hide Settings</a
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Info, Lock, LockOpen, X } from "@lucide/vue";
import { models, services } from "django-airavata-api";
import { mixins, utils } from "django-airavata-common-ui";
import { NATIVE_SELECT_CLASS } from "../../lib/utils";

export default {
  name: "queue-settings-editor",
  components: { Info, Lock, LockOpen, X },
  // VModelMixin supplies the `modelValue` prop and the `data` working copy and
  // emits `update:modelValue`; the parent binds with v-model. (Was a leftover
  // Vue 2 `value` prop — undefined under Vue 3, crashing mounted() below.)
  mixins: [mixins.VModelMixin],
  props: {
    appDeploymentId: {
      type: String,
      required: true,
    },
    appModuleId: {
      type: String,
      required: true,
    },
    computeResourcePolicy: {
      type: models.ComputeResourcePolicy,
      required: false,
    },
    batchQueueResourcePolicies: {
      type: Array,
      required: false,
    },
  },
  data() {
    return {
      showConfiguration: false,
      appDeploymentQueues: null,
      enableNodeCountToCpuCheck: true,
      applicationInterface: null,
    };
  },
  computed: {
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>, plus the
      // invalid-state ring so it mirrors `:aria-invalid` on shadcn controls.
      return `${NATIVE_SELECT_CLASS} aria-invalid:border-destructive aria-invalid:ring-destructive/40`;
    },
    queueOptions: function () {
      const queueOptions = this.queueDefaults.map((queueDefault) => {
        return {
          value: queueDefault.queue_name,
          text: queueDefault.queue_name,
        };
      });
      return queueOptions;
    },
    selectedQueueDefault: function () {
      return this.queueDefaults.find(
        (queue) => queue.queue_name === this.data.queue_name,
      );
    },
    maxCPUCount: function () {
      if (!this.selectedQueueDefault) {
        return 0;
      }
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_cores,
          this.selectedQueueDefault.max_processors,
        );
      }
      return this.selectedQueueDefault.max_processors;
    },
    maxNodes: function () {
      if (!this.selectedQueueDefault) {
        return 0;
      }
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_nodes,
          this.selectedQueueDefault.max_nodes,
        );
      }
      return this.selectedQueueDefault.max_nodes;
    },
    maxWalltime: function () {
      if (!this.selectedQueueDefault) {
        return 0;
      }
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_walltime,
          this.selectedQueueDefault.max_run_time,
        );
      }
      return this.selectedQueueDefault.max_run_time;
    },
    maxPhysicalMemory: function () {
      if (!this.selectedQueueDefault) {
        return 0;
      }
      return this.selectedQueueDefault.max_memory;
    },
    queueDefaults() {
      return this.appDeploymentQueues
        ? this.appDeploymentQueues
            .filter((q) => this.isQueueInComputeResourcePolicy(q.queue_name))
            .sort((a, b) => {
              // Sort default first, then by alphabetically by name
              if (a.is_default_queue) {
                return -1;
              } else if (b.is_default_queue) {
                return 1;
              } else {
                return a.queue_name.localeCompare(b.queue_name);
              }
            })
        : [];
    },
    defaultQueue() {
      if (this.queueDefaults.length === 0) {
        return null;
      }
      return this.queueDefaults[0];
    },
    batchQueueResourcePolicy() {
      if (!this.selectedQueueDefault) {
        return null;
      }
      return this.getBatchQueueResourcePolicy(
        this.selectedQueueDefault.queue_name,
      );
    },
    queueDescription() {
      return this.selectedQueueDefault
        ? this.selectedQueueDefault.queue_description
        : null;
    },
    validation() {
      // Don't run validation if we don't have selectedQueueDefault
      if (!this.selectedQueueDefault) {
        return this.data.validate();
      }
      return this.data.validate(
        this.selectedQueueDefault,
        this.batchQueueResourcePolicy,
      );
    },
    valid() {
      return Object.keys(this.validation).length === 0;
    },
    showQueueSettings() {
      return this.applicationInterface
        ? this.applicationInterface.show_queue_settings
        : false;
    },
    disabled() {
      return (
        this.applicationInterface &&
        !!this.applicationInterface.queue_settings_calculator_id
      );
    },
  },
  methods: {
    queueChanged: function (queueName) {
      const queueDefault = this.queueDefaults.find(
        (queue) => queue.queue_name === queueName,
      );
      this.data.total_cpu_count = this.getDefaultCPUCount(queueDefault);
      this.data.node_count = this.getDefaultNodeCount(queueDefault);
      this.data.wall_time_limit = this.getDefaultWalltime(queueDefault);
      if (this.maxPhysicalMemory === 0) {
        this.data.total_physical_memory = 0;
      }
    },
    validate() {
      if (!this.valid) {
        this.$emit("invalid");
      } else {
        this.$emit("valid");
      }
    },
    loadAppDeploymentQueues() {
      return services.ApplicationDeploymentService.getQueues({
        lookup: this.appDeploymentId,
      }).then((queueDefaults) => (this.appDeploymentQueues = queueDefaults));
    },
    setDefaultQueue() {
      if (this.queueDefaults.length === 0) {
        this.data.queue_name = null;
        return;
      }
      const defaultQueue = this.queueDefaults[0];

      this.data.queue_name = defaultQueue.queue_name;
      this.data.total_cpu_count = this.getDefaultCPUCount(defaultQueue);
      this.data.node_count = this.getDefaultNodeCount(defaultQueue);
      this.data.wall_time_limit = this.getDefaultWalltime(defaultQueue);
      if (this.maxPhysicalMemory === 0) {
        this.data.total_physical_memory = 0;
      }
    },
    isQueueInComputeResourcePolicy: function (queueName) {
      if (!this.computeResourcePolicy) {
        return true;
      }
      return this.computeResourcePolicy.allowed_batch_queues.includes(
        queueName,
      );
    },
    getBatchQueueResourcePolicy: function (queueName) {
      if (
        !this.batchQueueResourcePolicies ||
        this.batchQueueResourcePolicies.length === 0
      ) {
        return null;
      }
      return this.batchQueueResourcePolicies.find(
        (bqrp) => bqrp.queuename === queueName,
      );
    },
    getDefaultCPUCount: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_cores,
          queueDefault.default_cpu_count,
        );
      }
      return queueDefault.default_cpu_count;
    },
    getDefaultNodeCount: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_nodes,
          queueDefault.default_node_count,
        );
      }
      return queueDefault.default_node_count;
    },
    getDefaultWalltime: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_walltime,
          queueDefault.default_walltime,
        );
      }
      return queueDefault.default_walltime;
    },
    getValidationFeedback: function (properties) {
      return utils.getProperty(this.validation, properties);
    },
    getValidationState: function (properties, showValidState) {
      return this.getValidationFeedback(properties)
        ? false
        : showValidState
          ? true
          : null;
    },
    applyBatchQueueResourcePolicy() {
      // Apply batchQueueResourcePolicy maximums
      if (this.selectedQueueDefault) {
        this.data.total_cpu_count = Math.min(
          this.data.total_cpu_count,
          this.maxCPUCount,
        );
        this.data.node_count = Math.min(this.data.node_count, this.maxNodes);
        this.data.wall_time_limit = Math.min(
          this.data.wall_time_limit,
          this.maxWalltime,
        );
      }
    },
    nodeCountChanged() {
      if (
        this.enableNodeCountToCpuCheck &&
        this.selectedQueueDefault.cpu_per_node > 0
      ) {
        const nodeCount = parseInt(this.data.node_count);
        this.data.total_cpu_count = Math.min(
          nodeCount * this.selectedQueueDefault.cpu_per_node,
          this.maxCPUCount,
        );
      }
    },
    cpuCountChanged() {
      if (
        this.enableNodeCountToCpuCheck &&
        this.selectedQueueDefault.cpu_per_node > 0
      ) {
        const cpuCount = parseInt(this.data.total_cpu_count);
        if (cpuCount > 0) {
          this.data.node_count = Math.min(
            Math.ceil(cpuCount / this.selectedQueueDefault.cpu_per_node),
            this.maxNodes,
          );
        }
      }
    },
    loadApplicationInterface() {
      services.ApplicationModuleService.getApplicationInterface({
        lookup: this.appModuleId,
      }).then(
        (applicationInterface) =>
          (this.applicationInterface = applicationInterface),
      );
    },
  },
  watch: {
    enableNodeCountToCpuCheck() {
      if (this.enableNodeCountToCpuCheck) {
        this.nodeCountChanged();
      }
    },
    appDeploymentId() {
      this.loadAppDeploymentQueues().then(() => this.setDefaultQueue());
    },
    // If batch queue policy changes, apply any maximum values to current values
    batchQueueResourcePolicy(value, oldValue) {
      if (
        value &&
        (!oldValue || value.resource_policy_id !== oldValue.resource_policy_id)
      ) {
        this.applyBatchQueueResourcePolicy();
      }
    },
    computeResourcePolicy() {
      if (!this.isQueueInComputeResourcePolicy(this.data.queue_name)) {
        this.setDefaultQueue();
      }
    },
    modelValue: {
      // Rerun validation whenever the queue settings change, which can from
      // outside the component, for example when a queue settings calculator
      // provides values
      handler() {
        this.validate();
      },
      deep: true,
    },
    // Re-validate on internal edits of the working copy. (Replaces the Vue 2
    // `this.$on("input", ...)` self-listener, which is removed in Vue 3.)
    data: {
      handler() {
        this.validate();
      },
      deep: true,
    },
  },
  mounted: function () {
    this.loadAppDeploymentQueues().then(() => {
      // For brand new queue settings (no queueName specified) load the default
      // queue and its default values and apply them
      if (!this.modelValue.queue_name) {
        this.setDefaultQueue();
      }
    });
    this.loadApplicationInterface();
  },
};
</script>

<style></style>
