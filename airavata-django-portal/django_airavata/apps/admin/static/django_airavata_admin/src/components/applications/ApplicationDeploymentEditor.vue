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
          class="mt-2 mb-2"
          v-if="localSharedEntity"
          :shared-entity="localSharedEntity"
          @saved="savedSharedEntity"
          @unsaved="unsavedSharedEntity"
        />
        <form-group
          label="Application Executable Path"
          label-for="executable-path"
        >
          <input class="form-control"
            id="executable-path"
            type="text"
            v-model="data.executablePath"
            required
            :disabled="readonly"
          />
        </form-group>
        <form-group
          label="Application Parallelism Type"
          label-for="parallelism-type"
        >
          <select class="form-select"
            id="parallelism-type"
            v-model="data.parallelism"
            :options="parallelismTypeOptions"
            :disabled="readonly"
          />
        </form-group>
        <form-group
          label="Application Deployment Description"
          label-for="deployment-description"
        >
          <textarea class="form-control"
            id="deployment-description"
            v-model="data.appDeploymentDescription"
            :rows="3"
            :disabled="readonly"
          ></textarea>
        </form-group>
        <command-objects-editor
          title="Module Load Commands"
          add-button-label="Add Module Load Command"
          v-model="data.moduleLoadCmds"
          :readonly="readonly"
        />
        <set-env-paths-editor
          title="Library Prepend Paths"
          add-button-label="Add a Library Prepend Path"
          v-model="data.libPrependPaths"
          :readonly="readonly"
        />
        <set-env-paths-editor
          title="Library Append Paths"
          add-button-label="Add a Library Append Path"
          v-model="data.libAppendPaths"
          :readonly="readonly"
        />
        <set-env-paths-editor
          title="Environment Variables"
          add-button-label="Add Environment Variable"
          v-model="data.setEnvironment"
          :readonly="readonly"
        />
        <command-objects-editor
          title="Pre Job Commands"
          add-button-label="Add Pre Job Command"
          v-model="data.preJobCommands"
          :readonly="readonly"
        />
        <command-objects-editor
          title="Post Job Commands"
          add-button-label="Add Post Job Command"
          v-model="data.postJobCommands"
          :readonly="readonly"
        />
        <div class="mb-3" label="Default Queue Name" label-for="default-queue-name">
          <select class="form-select"
            id="default-queue-name"
            v-model="data.defaultQueueName"
            @change="defaultQueueChanged"
            :disabled="readonly"
          >
            <option :value="null">Select a Default Queue</option>
            <option v-for="opt in queueNameOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
          </select>
        </div>
        <div class="mb-3" label="Default Node Count" label-for="default-node-count">
          <input class="form-control"
            id="default-node-count"
            type="number"
            v-model="data.defaultNodeCount"
            min="0"
            :max="maxNodes"
            :disabled="defaultQueueAttributesDisabled"
          />
        </div>
        <div class="mb-3" label="Default CPU Count" label-for="default-cpu-count">
          <input class="form-control"
            id="default-cpu-count"
            type="number"
            v-model="data.defaultCPUCount"
            min="0"
            :max="maxCPUCount"
            :disabled="defaultQueueAttributesDisabled"
          />
          <small class="form-text text-muted" v-if="cpuPerNode > 0">
            There are {{ cpuPerNode }} cores per node.
          </small>
        </div>
        <form-group
          label="Default Walltime (in minutes)"
          label-for="default-walltime"
        >
          <input class="form-control"
            id="default-walltime"
            type="number"
            v-model="data.defaultWalltime"
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
  name: "application-deployment-editor",
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
  components: {
    CommandObjectsEditor,
    SetEnvPathsEditor,
    "share-button": components.ShareButton,
  },
  data() {
    return {
      computeResource: null,
      localSharedEntity: this.sharedEntity ? this.sharedEntity.clone() : null,
      dirty: false,
    };
  },
  mounted() {
    this.$on("input", () => {
      this.dirty = true;
    });
  },
  destroyed() {
    this.$off("input");
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
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.defaultQueueName
          )
        : null;
      return queue ? queue.max_nodes : 0;
    },
    maxCPUCount() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.defaultQueueName
          )
        : null;
      return queue ? queue.max_processors : 0;
    },
    maxWalltime() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.defaultQueueName
          )
        : null;
      return queue ? queue.max_run_time : 0;
    },
    cpuPerNode() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.defaultQueueName
          )
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
      return this.owner ? this.owner.userId : null;
    },
    ownerTitle() {
      return this.owner
        ? this.owner.firstName +
            " " +
            this.owner.lastName +
            " (" +
            this.owner.email +
            ")"
        : null;
    },
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
        const queue = this.computeResource.batch_queues.find(
          (q) => q.queue_name === queueName
        );
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
  watch: {
    sharedEntity(newValue) {
      this.localSharedEntity = newValue.clone();
    },
  },
};
</script>
