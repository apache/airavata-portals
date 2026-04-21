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
          @change="queueChanged($event.target.value)"
          @input.stop
        >
          <option v-for="opt in queueOptions" :key="opt.value" :value="opt.value">
            {{ opt.text }}
          </option>
        </select>
        <div slot="description">{{ queueDescription }}</div>
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
            <div slot="description">
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
            <div slot="description">
              <i class="fa fa-info-circle" aria-hidden="true"></i>
              Max Allowed Cores = {{ maxAllowedCores
              }}<template v-if="queue && queue.cpuPerNode > 0"
                >. There are {{ queue.cpuPerNode }} cores per node.
              </template>
            </div>
          </div>
        </div>
        <div v-if="queue && queue.cpuPerNode > 0" class="d-flex flex-column">
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
        <div slot="description">
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
        <div slot="description">
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

<script>
import { utils } from "django-airavata-api";

import store from "./store";
import { mapGetters } from "vuex";

export default {
  store: store,
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
  data() {
    return {
      showConfiguration: false,
      enableNodeCountToCpuCheck: true,
    };
  },
  created() {
    this.$store.dispatch("initializeQueueSettings", {
      queueName: this.queueName,
      nodeCount: this.nodeCount,
      totalCPUCount: this.totalCPUCount,
      wallTimeLimit: this.wallTimeLimit,
      totalPhysicalMemory: this.totalPhysicalMemory,
    });
  },
  computed: {
    ...mapGetters({
      queue: "queue",
      queues: "queues",
      maxAllowedCores: "maxAllowedCores",
      maxAllowedNodes: "maxAllowedNodes",
      maxAllowedWalltime: "maxAllowedWalltime",
      maxMemory: "maxMemory",
      selectedQueueName: "queueName",
      getTotalCPUCount: "totalCPUCount",
      getNodeCount: "nodeCount",
      getWallTimeLimit: "wallTimeLimit",
      getTotalPhysicalMemory: "totalPhysicalMemory",
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
          value: q.queueName,
          text: q.queueName,
        };
      });
      utils.StringUtils.sortIgnoreCase(queueOptions, (q) => q.text);
      return queueOptions;
    },
    queueDescription() {
      return this.queue ? this.queue.queueDescription : null;
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
      this.$store.dispatch("updateQueueName", { queueName });
    },
    updateNodeCount(event) {
      this.$store.dispatch("updateNodeCount", {
        nodeCount: event.target.value,
        enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
      });
    },
    updateTotalCPUCount(event) {
      this.$store.dispatch("updateTotalCPUCount", {
        totalCPUCount: event.target.value,
        enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
      });
    },
    updateWallTimeLimit(event) {
      this.$store.dispatch("updateWallTimeLimit", {
        wallTimeLimit: event.target.value,
      });
    },
    updateTotalPhysicalMemory(event) {
      this.$store.dispatch("updateTotalPhysicalMemory", {
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
        this.$store.dispatch("updateNodeCount", {
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
        this.$store.dispatch("updateNodeCount", {
          nodeCount: value,
          enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
        });
      }
    },
    totalCPUCount(value) {
      if (value && this.getTotalCPUCount !== value) {
        this.$store.dispatch("updateTotalCPUCount", {
          totalCPUCount: value,
          enableNodeCountToCpuCheck: this.enableNodeCountToCpuCheck,
        });
      }
    },
    wallTimeLimit(value) {
      if (value && this.getWallTimeLimit !== value) {
        this.$store.dispatch("updateWallTimeLimit", { wallTimeLimit: value });
      }
    },
    totalPhysicalMemory(value) {
      if (value && this.getTotalPhysicalMemory !== value) {
        this.$store.dispatch("updateTotalPhysicalMemory", {
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
