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

<script>
import { models, services } from "django-airavata-api";
import { mixins, utils } from "django-airavata-common-ui";

export default {
  name: "QueueSettingsEditor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.ComputationalResourceSchedulingModel,
    },
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
      return this.queueDefaults.find((queue) => queue.queue_name === this.data.queue_name);
    },
    maxCPUCount: function () {
      if (!this.selectedQueueDefault) {
        return 0;
      }
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.maxAllowedCores,
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
          batchQueueResourcePolicy.maxAllowedNodes,
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
          batchQueueResourcePolicy.maxAllowedWalltime,
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
      return this.getBatchQueueResourcePolicy(this.selectedQueueDefault.queue_name);
    },
    queueDescription() {
      return this.selectedQueueDefault ? this.selectedQueueDefault.queue_description : null;
    },
    validation() {
      // Don't run validation if we don't have selectedQueueDefault
      if (!this.selectedQueueDefault) {
        return this.data.validate();
      }
      return this.data.validate(this.selectedQueueDefault, this.batchQueueResourcePolicy);
    },
    valid() {
      return Object.keys(this.validation).length === 0;
    },
    showQueueSettings() {
      return this.applicationInterface ? this.applicationInterface.show_queue_settings : false;
    },
    disabled() {
      return this.applicationInterface && !!this.applicationInterface.queue_settings_calculator_id;
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
      if (value && (!oldValue || value.resourcePolicyId !== oldValue.resourcePolicyId)) {
        this.applyBatchQueueResourcePolicy();
      }
    },
    computeResourcePolicy() {
      if (!this.isQueueInComputeResourcePolicy(this.data.queue_name)) {
        this.setDefaultQueue();
      }
    },
    value: {
      // Rerun validation whenever the queue settings change, which can from
      // outside the component, for example when a queue settings calculator
      // provides values
      handler() {
        this.validate();
      },
      deep: true,
    },
  },
  mounted: function () {
    this.loadAppDeploymentQueues().then(() => {
      // For brand new queue settings (no queue_name specified) load the default
      // queue and its default values and apply them
      if (!this.value.queue_name) {
        this.setDefaultQueue();
      }
    });
    this.$on("input", () => this.validate());
    this.loadApplicationInterface();
  },
  methods: {
    queueChanged: function (queueName) {
      const queueDefault = this.queueDefaults.find((queue) => queue.queue_name === queueName);
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
    isQueueInComputeResourcePolicy: function (queue_name) {
      if (!this.computeResourcePolicy) {
        return true;
      }
      return this.computeResourcePolicy.allowedBatchQueues.includes(queue_name);
    },
    getBatchQueueResourcePolicy: function (queueName) {
      if (!this.batchQueueResourcePolicies || this.batchQueueResourcePolicies.length === 0) {
        return null;
      }
      return this.batchQueueResourcePolicies.find((bqrp) => bqrp.queuename === queueName);
    },
    getDefaultCPUCount: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(batchQueueResourcePolicy.maxAllowedCores, queueDefault.default_cpu_count);
      }
      return queueDefault.default_cpu_count;
    },
    getDefaultNodeCount: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(batchQueueResourcePolicy.maxAllowedNodes, queueDefault.default_node_count);
      }
      return queueDefault.default_node_count;
    },
    getDefaultWalltime: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(batchQueueResourcePolicy.maxAllowedWalltime, queueDefault.default_walltime);
      }
      return queueDefault.default_walltime;
    },
    getValidationFeedback: function (properties) {
      return utils.getProperty(this.validation, properties);
    },
    getValidationState: function (properties, showValidState) {
      return this.getValidationFeedback(properties) ? false : showValidState ? true : null;
    },
    applyBatchQueueResourcePolicy() {
      // Apply batchQueueResourcePolicy maximums
      if (this.selectedQueueDefault) {
        this.data.total_cpu_count = Math.min(this.data.total_cpu_count, this.maxCPUCount);
        this.data.node_count = Math.min(this.data.node_count, this.maxNodes);
        this.data.wall_time_limit = Math.min(this.data.wall_time_limit, this.maxWalltime);
      }
    },
    nodeCountChanged() {
      if (this.enableNodeCountToCpuCheck && this.selectedQueueDefault.cpu_per_node > 0) {
        const nodeCount = parseInt(this.data.node_count);
        this.data.total_cpu_count = Math.min(
          nodeCount * this.selectedQueueDefault.cpu_per_node,
          this.maxCPUCount,
        );
      }
    },
    cpuCountChanged() {
      if (this.enableNodeCountToCpuCheck && this.selectedQueueDefault.cpu_per_node > 0) {
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
      }).then((applicationInterface) => (this.applicationInterface = applicationInterface));
    },
  },
};
</script>

<style></style>
