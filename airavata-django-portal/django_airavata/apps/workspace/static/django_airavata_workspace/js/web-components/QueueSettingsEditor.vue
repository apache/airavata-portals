<template>
  <div v-if="showQueueSettings">
    <div class="rounded-xl border bg-card text-card-foreground shadow-sm">
      <a
        href="#"
        class="block text-foreground"
        @click.prevent="showConfiguration = !showConfiguration"
      >
        <div class="p-6">
          <h5 class="mb-4 text-lg font-semibold">
            Settings for queue {{ selectedQueueName }}
          </h5>
          <div class="flex flex-wrap gap-4">
            <div class="flex-1">
              <h3 class="mb-0 text-lg font-semibold">
                {{ getNodeCount }}
              </h3>
              <span class="text-muted-foreground uppercase">NODE COUNT</span>
            </div>
            <div class="flex-1">
              <h3 class="mb-0 text-lg font-semibold">
                {{ getTotalCPUCount }}
              </h3>
              <span class="text-muted-foreground uppercase">CORE COUNT</span>
            </div>
            <div class="flex-1">
              <h3 class="mb-0 text-lg font-semibold">
                {{ getWallTimeLimit }} minutes
              </h3>
              <span class="text-muted-foreground uppercase">TIME LIMIT</span>
            </div>
            <div class="flex-1" v-if="maxMemory > 0">
              <h3 class="mb-0 text-lg font-semibold">
                {{ getTotalPhysicalMemory }} MB
              </h3>
              <span class="text-muted-foreground uppercase"
                >PHYSICAL MEMORY</span
              >
            </div>
          </div>
        </div>
      </a>
    </div>
    <div v-if="showConfiguration" class="mt-4">
      <div class="space-y-1.5">
        <label for="queue" class="text-sm leading-none font-medium select-none"
          >Select a Queue</label
        >
        <select
          id="queue"
          :value="selectedQueueName"
          required
          :class="nativeSelectClass"
          @change="queueChanged($event.target.value)"
        >
          <option
            v-for="option in queueOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.text }}
          </option>
        </select>
        <p class="text-sm text-muted-foreground">{{ queueDescription }}</p>
      </div>
      <div class="mt-4 flex flex-row">
        <div class="flex-1">
          <div class="space-y-1.5">
            <label
              for="node-count"
              class="text-sm leading-none font-medium select-none"
              >Node Count</label
            >
            <input
              id="node-count"
              type="number"
              min="1"
              :max="maxAllowedNodes"
              :value="getNodeCount"
              required
              :class="nativeInputClass"
              @input="updateNodeCount"
            />
            <p class="text-sm text-muted-foreground">
              <Info class="inline size-4" aria-hidden="true" />
              Max Allowed Nodes = {{ maxAllowedNodes }}
            </p>
          </div>
          <div class="mt-4 space-y-1.5">
            <label
              for="core-count"
              class="text-sm leading-none font-medium select-none"
              >Total Core Count</label
            >
            <input
              id="core-count"
              type="number"
              min="1"
              :max="maxAllowedCores"
              :value="getTotalCPUCount"
              required
              :class="nativeInputClass"
              @input="updateTotalCPUCount"
            />
            <p class="text-sm text-muted-foreground">
              <Info class="inline size-4" aria-hidden="true" />
              Max Allowed Cores = {{ maxAllowedCores
              }}<template v-if="queue && queue.cpu_per_node > 0"
                >. There are {{ queue.cpu_per_node }} cores per node.
              </template>
            </p>
          </div>
        </div>
        <div class="flex flex-col" v-if="queue && queue.cpu_per_node > 0">
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
          <button
            type="button"
            class="inline-flex size-8 items-center justify-center rounded-full border border-input bg-background text-sm shadow-xs transition-all hover:bg-accent hover:text-accent-foreground"
            v-on:click="enableNodeCountToCpuCheck = !enableNodeCountToCpuCheck"
          >
            <Lock
              v-if="enableNodeCountToCpuCheck"
              class="size-4"
              aria-hidden="true"
            />
            <LockOpen v-else class="size-4" aria-hidden="true" />
          </button>
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
        <label
          for="walltime-limit"
          class="text-sm leading-none font-medium select-none"
          >Wall Time Limit</label
        >
        <div class="flex">
          <input
            id="walltime-limit"
            type="number"
            min="1"
            :max="maxAllowedWalltime"
            :value="getWallTimeLimit"
            required
            :class="nativeInputGroupClass"
            @input="updateWallTimeLimit"
          />
          <span
            class="flex items-center rounded-r-md border border-l-0 border-input px-3 text-sm text-muted-foreground"
            >minutes</span
          >
        </div>
        <p class="text-sm text-muted-foreground">
          <Info class="inline size-4" aria-hidden="true" />
          Max Allowed Wall Time = {{ maxAllowedWalltime }} minutes
        </p>
      </div>
      <div class="mt-4 space-y-1.5" v-if="maxMemory > 0">
        <label
          for="total-physical-memory"
          class="text-sm leading-none font-medium select-none"
          >Total Physical Memory</label
        >
        <div class="flex">
          <input
            id="total-physical-memory"
            type="number"
            min="0"
            :max="maxMemory"
            :value="getTotalPhysicalMemory"
            :class="nativeInputGroupClass"
            @input="updateTotalPhysicalMemory"
          />
          <span
            class="flex items-center rounded-r-md border border-l-0 border-input px-3 text-sm text-muted-foreground"
            >MB</span
          >
        </div>
        <p class="text-sm text-muted-foreground">
          <Info class="inline size-4" aria-hidden="true" />
          Max Physical Memory = {{ maxMemory }} MB
        </p>
      </div>
      <div class="mt-4">
        <a
          href="#"
          class="inline-flex items-center gap-1 text-muted-foreground"
          @click.prevent="showConfiguration = false"
        >
          <X class="size-4" aria-hidden="true" />
          Hide Settings</a
        >
      </div>
    </div>
  </div>
</template>

<script>
import { Info, Lock, LockOpen, X } from "@lucide/vue";
import { utils } from "django-airavata-api";
import { mapState } from "pinia";
import { useExperimentStore } from "./store";
import { cn, NATIVE_INPUT_CLASS, NATIVE_SELECT_CLASS } from "../lib/utils";

export default {
  components: { Info, Lock, LockOpen, X },
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
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>.
      return NATIVE_SELECT_CLASS;
    },
    nativeInputClass() {
      // Native number input (shadcn <Input> isn't registered in this standalone
      // web-component build) styled to match a shadcn <Input>.
      return NATIVE_INPUT_CLASS;
    },
    nativeInputGroupClass() {
      // Same as nativeInputClass but with a flat right edge so it sits flush
      // against a trailing unit (minutes / MB) addon.
      return cn(NATIVE_INPUT_CLASS, "rounded-r-none");
    },
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
