<template>
  <div v-if="showQueueSettings">
    <div class="row">
      <div class="col">
        <div
          class="card border-default"
          :class="{ 'border-danger': !valid, 'is-disabled': disabled }"
        >
          <b-link
            @click="showConfiguration = !showConfiguration"
            class="card-link text-dark"
            :disabled="disabled"
          >
            <div class="card-body">
              <h5 class="card-title mb-4">
                Settings for queue {{ data.queue_name }}
              </h5>
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
                <div class="col" v-if="maxPhysicalMemory > 0">
                  <h3 class="h5 mb-0">{{ data.total_physical_memory }} MB</h3>
                  <span class="text-muted text-uppercase">PHYSICAL MEMORY</span>
                </div>
              </div>
            </div>
          </b-link>
        </div>
      </div>
    </div>
    <div v-if="showConfiguration">
      <div class="row">
        <div class="col">
          <b-form-group
            label="Select a Queue"
            label-for="queue"
            :invalid-feedback="getValidationFeedback('queueName')"
            :state="getValidationState('queueName')"
          >
            <b-form-select
              id="queue"
              v-model="data.queue_name"
              :options="queueOptions"
              required
              @change="queueChanged"
              :state="getValidationState('queueName')"
            >
            </b-form-select>
            <div slot="description">
              {{ queueDescription }}
            </div>
          </b-form-group>
          <div class="d-flex flex-row">
            <div class="flex-fill">
              <b-form-group
                label="Node Count"
                label-for="node-count"
                :invalid-feedback="getValidationFeedback('nodeCount')"
                :state="getValidationState('nodeCount', true)"
              >
                <b-form-input
                  id="node-count"
                  type="number"
                  min="1"
                  :max="maxNodes"
                  v-model="data.node_count"
                  required
                  @input="nodeCountChanged"
                  :state="getValidationState('nodeCount', true)"
                >
                </b-form-input>
                <div slot="description">
                  <i class="fa fa-info-circle" aria-hidden="true"></i>
                  Max Allowed Nodes = {{ maxNodes }}
                </div>
              </b-form-group>
              <b-form-group
                label="Total Core Count"
                label-for="core-count"
                :invalid-feedback="getValidationFeedback('totalCPUCount')"
                :state="getValidationState('totalCPUCount', true)"
              >
                <b-form-input
                  id="core-count"
                  type="number"
                  min="1"
                  :max="maxCPUCount"
                  v-model="data.total_cpu_count"
                  required
                  @input="cpuCountChanged"
                  :state="getValidationState('totalCPUCount', true)"
                >
                </b-form-input>
                <div slot="description">
                  <i class="fa fa-info-circle" aria-hidden="true"></i>
                  Max Allowed Cores = {{ maxCPUCount
                  }}<template
                    v-if="
                      selectedQueueDefault &&
                      selectedQueueDefault.cpu_per_node > 0
                    "
                    >. There are {{ selectedQueueDefault.cpu_per_node }} cores per
                    node.
                  </template>
                </div>
              </b-form-group>
            </div>
            <div
              class="d-flex flex-column"
              v-if="selectedQueueDefault && selectedQueueDefault.cpu_per_node > 0"
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
              <b-button
                size="sm"
                pill
                variant="outline-secondary"
                v-on:click="
                  enableNodeCountToCpuCheck = !enableNodeCountToCpuCheck
                "
              >
                <i
                  v-if="enableNodeCountToCpuCheck"
                  class="fa fa-lock"
                  aria-hidden="true"
                ></i>
                <i v-else class="fa fa-unlock" aria-hidden="true"></i>
              </b-button>
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
          <b-form-group
            label="Wall Time Limit"
            label-for="walltime-limit"
            :invalid-feedback="getValidationFeedback('wallTimeLimit')"
            :state="getValidationState('wallTimeLimit', true)"
          >
            <b-input-group append="minutes">
              <b-form-input
                id="walltime-limit"
                type="number"
                min="1"
                :max="maxWalltime"
                v-model="data.wall_time_limit"
                required
                :state="getValidationState('wallTimeLimit', true)"
              >
              </b-form-input>
            </b-input-group>
            <div slot="description">
              <i class="fa fa-info-circle" aria-hidden="true"></i>
              Max Allowed Wall Time = {{ maxWalltime }} minutes
            </div>
          </b-form-group>
          <b-form-group
            v-if="maxPhysicalMemory > 0"
            label="Total Physical Memory"
            label-for="total-physical-memory"
            :invalid-feedback="getValidationFeedback('totalPhysicalMemory')"
            :state="getValidationState('totalPhysicalMemory', true)"
          >
            <b-input-group append="MB">
              <b-form-input
                id="total-physical-memory"
                type="number"
                min="0"
                :max="maxPhysicalMemory"
                v-model="data.total_physical_memory"
                :state="getValidationState('totalPhysicalMemory', true)"
              >
              </b-form-input>
            </b-input-group>
            <div slot="description">
              <i class="fa fa-info-circle" aria-hidden="true"></i>
              Max Physical Memory = {{ maxPhysicalMemory }} MB
            </div>
          </b-form-group>
          <div>
            <a
              class="text-secondary action-link"
              href="#"
              @click.prevent="showConfiguration = false"
            >
              <i class="fa fa-times text-secondary" aria-hidden="true"></i>
              Hide Settings</a
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { models, services } from "django-airavata-api";
import { mixins, utils } from "django-airavata-common-ui";

export default {
  name: "queue-settings-editor",
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
      return this.queueDefaults.find(
        (queue) => queue.queue_name === this.data.queue_name
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
          this.selectedQueueDefault.max_processors
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
          this.selectedQueueDefault.max_nodes
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
          this.selectedQueueDefault.max_run_time
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
        this.selectedQueueDefault.queue_name
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
        this.batchQueueResourcePolicy
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
        (queue) => queue.queue_name === queueName
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
      return this.computeResourcePolicy.allowed_batch_queues.includes(queueName);
    },
    getBatchQueueResourcePolicy: function (queueName) {
      if (
        !this.batchQueueResourcePolicies ||
        this.batchQueueResourcePolicies.length === 0
      ) {
        return null;
      }
      return this.batchQueueResourcePolicies.find(
        (bqrp) => bqrp.queuename === queueName
      );
    },
    getDefaultCPUCount: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_cores,
          queueDefault.default_cpu_count
        );
      }
      return queueDefault.default_cpu_count;
    },
    getDefaultNodeCount: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_nodes,
          queueDefault.default_node_count
        );
      }
      return queueDefault.default_node_count;
    },
    getDefaultWalltime: function (queueDefault) {
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_walltime,
          queueDefault.default_walltime
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
          this.maxCPUCount
        );
        this.data.node_count = Math.min(this.data.node_count, this.maxNodes);
        this.data.wall_time_limit = Math.min(
          this.data.wall_time_limit,
          this.maxWalltime
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
          this.maxCPUCount
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
            this.maxNodes
          );
        }
      }
    },
    loadApplicationInterface() {
      services.ApplicationModuleService.getApplicationInterface({
        lookup: this.appModuleId,
      }).then(
        (applicationInterface) =>
          (this.applicationInterface = applicationInterface)
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
      // For brand new queue settings (no queueName specified) load the default
      // queue and its default values and apply them
      if (!this.value.queue_name) {
        this.setDefaultQueue();
      }
    });
    this.$on("input", () => this.validate());
    this.loadApplicationInterface();
  },
};
</script>

<style></style>
