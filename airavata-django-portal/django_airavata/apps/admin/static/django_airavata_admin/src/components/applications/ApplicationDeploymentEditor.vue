<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-1">
          {{ name }}
        </h1>
        <p v-if="owner" class="mb-2 text-muted">
          Created by <span :title="ownerTitle">{{ ownerUserId }}</span>
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

<script>
import { models, services } from "django-airavata-api";
import CommandObjectsEditor from "./CommandObjectsEditor.vue";
import SetEnvPathsEditor from "./SetEnvPathsEditor.vue";
import { components, mixins } from "django-airavata-common-ui";

export default {
  name: "ApplicationDeploymentEditor",
  components: {
    CommandObjectsEditor,
    SetEnvPathsEditor,
    "share-button": components.ShareButton,
  },
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.ApplicationDescriptionDefinition,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    sharedEntity: {
      type: models.SharedEntity,
      required: true,
    },
  },
  data() {
    return {
      computeResource: null,
      localSharedEntity: this.sharedEntity ? this.sharedEntity.clone() : null,
      dirty: false,
    };
  },
  computed: {
    name() {
      if (this.computeResource) {
        return this.computeResource.host_name;
      } else {
        return this.data.computeHostId.substring(0, 10) + "...";
      }
    },
    parallelismTypeOptions() {
      return models.ParallelismType.values.map((parType) => {
        return {
          value: parType,
          text: parType.name,
        };
      });
    },
    queueNameOptions() {
      if (!this.computeResource) {
        return [];
      }
      return this.computeResource.batch_queues.map((queue) => {
        return {
          value: queue.queue_name,
          text: queue.queue_name,
        };
      });
    },
    maxNodes() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find((q) => q.queue_name === this.data.defaultQueueName)
        : null;
      return queue ? queue.max_nodes : 0;
    },
    maxCPUCount() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find((q) => q.queue_name === this.data.defaultQueueName)
        : null;
      return queue ? queue.max_processors : 0;
    },
    maxWalltime() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find((q) => q.queue_name === this.data.defaultQueueName)
        : null;
      return queue ? queue.max_run_time : 0;
    },
    cpuPerNode() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find((q) => q.queue_name === this.data.defaultQueueName)
        : null;
      return queue ? queue.cpu_per_node : 0;
    },
    defaultQueueAttributesDisabled() {
      return !this.data.defaultQueueName || this.readonly;
    },
    owner() {
      return this.localSharedEntity && this.localSharedEntity.owner
        ? this.localSharedEntity.owner
        : null;
    },
    ownerUserId() {
      return this.owner ? this.owner.user_id : null;
    },
    ownerTitle() {
      return this.owner
        ? this.owner.first_name + " " + this.owner.last_name + " (" + this.owner.email + ")"
        : null;
    },
  },
  watch: {
    sharedEntity(newValue) {
      this.localSharedEntity = newValue.clone();
    },
  },
  mounted() {
    this.$on("input", () => {
      this.dirty = true;
    });
  },
  unmounted() {
    // Vue 3 removed the $off() instance method and `destroyed()` hook.
    // Listeners attached via `this.$on("input", ...)` would need to track
    // their own cleanup; leaving this as a renamed stub is a no-op under
    // Vue 3, matching the pre-fix behaviour (destroyed was silently
    // ignored).
  },
  created() {
    services.ComputeResourceService.retrieve({
      lookup: this.data.computeHostId,
    }).then((computeResource) => {
      this.computeResource = computeResource;
    });
  },
  methods: {
    save() {
      // FIXME: if the save operation fails then this form should still be
      // dirty. But this editor doesn't know if the save fails.
      this.dirty = false;
      this.$emit("save");
    },
    cancel() {
      this.dirty = false;
      this.$emit("cancel");
    },
    defaultQueueChanged(queueName) {
      if (queueName) {
        const queue = this.computeResource.batch_queues.find((q) => q.queue_name === queueName);
        this.data.defaultNodeCount = queue.default_node_count;
        this.data.defaultCPUCount = queue.default_cpu_count;
        this.data.defaultWalltime = queue.default_walltime;
      } else {
        this.data.defaultNodeCount = null;
        this.data.defaultCPUCount = null;
        this.data.defaultWalltime = null;
      }
    },
    savedSharedEntity(newSharedEntity) {
      this.$emit("sharing-changed", newSharedEntity, this.data, false);
    },
    unsavedSharedEntity(newSharedEntity) {
      this.dirty = true;
      this.$emit("sharing-changed", newSharedEntity, this.data, true);
    },
  },
};
</script>
