<template>
  <div v-if="showQueueSettings">
    <div class="card border-default">
      <b-link
        @click="showConfiguration = !showConfiguration"
        class="card-link text-dark"
      >
        <div class="card-body">
          <h5 class="card-title mb-4">
            Settings for queue {{ selectedQueueName }}
          </h5>
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
            <div class="col" v-if="maxMemory > 0">
              <h3 class="h5 mb-0">{{ getTotalPhysicalMemory }} MB</h3>
              <span class="text-muted text-uppercase">PHYSICAL MEMORY</span>
            </div>
          </div>
        </div>
      </b-link>
    </div>
    <div v-if="showConfiguration">
      <b-form-group label="Select a Queue" label-for="queue">
        <b-form-select
          id="queue"
          :model-value="selectedQueueName"
          :options="queueOptions"
          required
          @change="queueChanged"
        >
        </b-form-select>
        <template #description>{{ queueDescription }}</template>
      </b-form-group>
      <div class="d-flex flex-row">
        <div class="flex-fill">
          <b-form-group label="Node Count" label-for="node-count">
            <b-form-input
              id="node-count"
              type="number"
              min="1"
              :max="maxAllowedNodes"
              :model-value="getNodeCount"
              required
              @input="updateNodeCount"
            >
            </b-form-input>
            <template #description>
              <i class="fa fa-info-circle" aria-hidden="true"></i>
              Max Allowed Nodes = {{ maxAllowedNodes }}
            </template>
          </b-form-group>
          <b-form-group label="Total Core Count" label-for="core-count">
            <b-form-input
              id="core-count"
              type="number"
              min="1"
              :max="maxAllowedCores"
              :model-value="getTotalCPUCount"
              required
              @input="updateTotalCPUCount"
            >
            </b-form-input>
            <template #description>
              <i class="fa fa-info-circle" aria-hidden="true"></i>
              Max Allowed Cores = {{ maxAllowedCores
              }}<template v-if="queue && queue.cpu_per_node > 0"
                >. There are {{ queue.cpu_per_node }} cores per node.
              </template>
            </template>
          </b-form-group>
        </div>
        <div class="d-flex flex-column" v-if="queue && queue.cpu_per_node > 0">
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
            v-on:click="enableNodeCountToCpuCheck = !enableNodeCountToCpuCheck"
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
      <b-form-group label="Wall Time Limit" label-for="walltime-limit">
        <b-input-group append="minutes">
          <b-form-input
            id="walltime-limit"
            type="number"
            min="1"
            :max="maxAllowedWalltime"
            :model-value="getWallTimeLimit"
            required
            @input="updateWallTimeLimit"
          >
          </b-form-input>
        </b-input-group>
        <template #description>
          <i class="fa fa-info-circle" aria-hidden="true"></i>
          Max Allowed Wall Time = {{ maxAllowedWalltime }} minutes
        </template>
      </b-form-group>
      <b-form-group
        v-if="maxMemory > 0"
        label="Total Physical Memory"
        label-for="total-physical-memory"
      >
        <b-input-group append="MB">
          <b-form-input
            id="total-physical-memory"
            type="number"
            min="0"
            :max="maxMemory"
            :model-value="getTotalPhysicalMemory"
            @input="updateTotalPhysicalMemory"
          >
          </b-form-input>
        </b-input-group>
        <template #description>
          <i class="fa fa-info-circle" aria-hidden="true"></i>
          Max Physical Memory = {{ maxMemory }} MB
        </template>
      </b-form-group>
      <div>
        <b-link class="text-secondary" @click="showConfiguration = false">
          <i class="fa fa-times" aria-hidden="true"></i>
          Hide Settings</b-link
        >
      </div>
    </div>
  </div>
</template>

<script>
import { utils } from "django-airavata-api";
import { mapState } from "pinia";
import { useExperimentStore } from "./store";

export default {
  props: {
    queueName: {
      type: String,
    },
    nodeCount: {
      type: String,
    },
    "total-cpu-count": {
      type: String,
    },
    wallTimeLimit: {
      type: String,
    },
    totalPhysicalMemory: {
      type: String,
    },
  },
  created() {
    useExperimentStore().initializeQueueSettings({
      queueName: this.queueName,
      nodeCount: this.nodeCount,
      totalCPUCount: this.totalCPUCount,
      wallTimeLimit: this.wallTimeLimit,
      totalPhysicalMemory: this.totalPhysicalMemory,
    });
  },
  data() {
    return {
      showConfiguration: false,
      enableNodeCountToCpuCheck: true,
    };
  },
  computed: {
    ...mapState(useExperimentStore, {
      queue: "queue",
      queues: "queues",
      maxAllowedCores: "maxAllowedCores",
      maxAllowedNodes: "maxAllowedNodes",
      maxAllowedWalltime: "maxAllowedWalltime",
      maxMemory: "maxMemory",
      selectedQueueName: "getQueueName",
      getTotalCPUCount: "getTotalCPUCount",
      getNodeCount: "getNodeCount",
      getWallTimeLimit: "getWallTimeLimit",
      getTotalPhysicalMemory: "getTotalPhysicalMemory",
      showQueueSettings: "showQueueSettings",
    }),
    totalCPUCount() {
      return this.totalCpuCount;
    },
    queueOptions() {
      if (!this.queues) {
        return [];
      }
      const queueOptions = this.queues.map((q) => {
        return {
          value: q.queue_name,
          text: q.queue_name,
        };
      });
      utils.StringUtils.sortIgnoreCase(queueOptions, (q) => q.text);
      return queueOptions;
    },
    queueDescription() {
      return this.queue ? this.queue.queue_description : null;
    },
    currentQueueSettings() {
      return {
        queueName: this.selectedQueueName,
        totalCPUCount: this.getTotalCPUCount,
        nodeCount: this.getNodeCount,
        wallTimeLimit: this.getWallTimeLimit,
        totalPhysicalMemory: this.getTotalPhysicalMemory,
      };
    },
  },
  methods: {
    queueChanged(queueName) {
      useExperimentStore().updateQueueName({ queueName });
    },
    // TODO(vue3-migration): under bootstrap-vue-next, b-form-input @input passes
    // the value (not the native event). The web-component build is deferred
    // (Track D); these handlers read event.target.value and must be re-verified
    // when that build is migrated.
    updateNodeCount(event) {
      useExperimentStore().updateNodeCount({
        nodeCount: event.target.value,
        enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
      });
    },
    updateTotalCPUCount(event) {
      useExperimentStore().updateTotalCPUCount({
        totalCPUCount: event.target.value,
        enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
      });
    },
    updateWallTimeLimit(event) {
      useExperimentStore().updateWallTimeLimit({
        wallTimeLimit: event.target.value,
      });
    },
    updateTotalPhysicalMemory(event) {
      useExperimentStore().updateTotalPhysicalMemory({
        totalPhysicalMemory: event.target.value,
      });
    },
    emitValueChanged: function () {
      const inputEvent = new CustomEvent("input", {
        detail: [this.currentQueueSettings],
        composed: true,
        bubbles: true,
      });
      this.$el.dispatchEvent(inputEvent);
    },
  },
  watch: {
    enableNodeCountToCpuCheck() {
      if (this.enableNodeCountToCpuCheck) {
        useExperimentStore().updateNodeCount({
          nodeCount: this.getNodeCount,
          enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
        });
      }
    },
    queueName(value) {
      if (value && this.selectedQueueName !== value) {
        this.queueChanged(value);
      }
    },
    nodeCount(value) {
      if (value && this.getNodeCount !== value) {
        useExperimentStore().updateNodeCount({
          nodeCount: value,
          enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
        });
      }
    },
    totalCPUCount(value) {
      if (value && this.getTotalCPUCount !== value) {
        useExperimentStore().updateTotalCPUCount({
          totalCPUCount: value,
          enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
        });
      }
    },
    wallTimeLimit(value) {
      if (value && this.getWallTimeLimit !== value) {
        useExperimentStore().updateWallTimeLimit({ wallTimeLimit: value });
      }
    },
    totalPhysicalMemory(value) {
      if (value && this.getTotalPhysicalMemory !== value) {
        useExperimentStore().updateTotalPhysicalMemory({
          totalPhysicalMemory: value,
        });
      }
    },
    currentQueueSettings() {
      this.emitValueChanged();
    },
  },
};
</script>

<style lang="scss">
@import "./styles";

:host {
  display: block;
  margin-bottom: 1rem;
}
</style>
