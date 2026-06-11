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
        <b-form-group
          label="Application Executable Path"
          label-for="executable-path"
        >
          <b-form-input
            id="executable-path"
            type="text"
            v-model="data.executable_path"
            required
            :disabled="readonly"
          ></b-form-input>
        </b-form-group>
        <b-form-group
          label="Application Parallelism Type"
          label-for="parallelism-type"
        >
          <b-form-select
            id="parallelism-type"
            v-model="data.parallelism"
            :options="parallelismTypeOptions"
            :disabled="readonly"
          />
        </b-form-group>
        <b-form-group
          label="Application Deployment Description"
          label-for="deployment-description"
        >
          <b-form-textarea
            id="deployment-description"
            v-model="data.app_deployment_description"
            :rows="3"
            :disabled="readonly"
          ></b-form-textarea>
        </b-form-group>
        <command-objects-editor
          title="Module Load Commands"
          add-button-label="Add Module Load Command"
          v-model="data.module_load_cmds"
          :readonly="readonly"
        />
        <set-env-paths-editor
          title="Library Prepend Paths"
          add-button-label="Add a Library Prepend Path"
          v-model="data.lib_prepend_paths"
          :readonly="readonly"
        />
        <set-env-paths-editor
          title="Library Append Paths"
          add-button-label="Add a Library Append Path"
          v-model="data.lib_append_paths"
          :readonly="readonly"
        />
        <set-env-paths-editor
          title="Environment Variables"
          add-button-label="Add Environment Variable"
          v-model="data.set_environment"
          :readonly="readonly"
        />
        <command-objects-editor
          title="Pre Job Commands"
          add-button-label="Add Pre Job Command"
          v-model="data.pre_job_commands"
          :readonly="readonly"
        />
        <command-objects-editor
          title="Post Job Commands"
          add-button-label="Add Post Job Command"
          v-model="data.post_job_commands"
          :readonly="readonly"
        />
        <b-form-group label="Default Queue Name" label-for="default-queue-name">
          <b-form-select
            id="default-queue-name"
            v-model="data.default_queue_name"
            :options="queueNameOptions"
            @change="defaultQueueChanged"
            :disabled="readonly"
          >
            <template slot="first">
              <option :value="null">Select a Default Queue</option>
            </template>
          </b-form-select>
        </b-form-group>
        <b-form-group label="Default Node Count" label-for="default-node-count">
          <b-form-input
            id="default-node-count"
            type="number"
            v-model="data.default_node_count"
            min="0"
            :max="maxNodes"
            :disabled="defaultQueueAttributesDisabled"
          ></b-form-input>
        </b-form-group>
        <b-form-group label="Default CPU Count" label-for="default-cpu-count">
          <b-form-input
            id="default-cpu-count"
            type="number"
            v-model="data.default_cpu_count"
            min="0"
            :max="maxCPUCount"
            :disabled="defaultQueueAttributesDisabled"
          ></b-form-input>
          <template #description v-if="cpuPerNode > 0">
            There are {{ cpuPerNode }} cores per node.
          </template>
        </b-form-group>
        <b-form-group
          label="Default Walltime (in minutes)"
          label-for="default-walltime"
        >
          <b-form-input
            id="default-walltime"
            type="number"
            v-model="data.default_walltime"
            min="0"
            :max="maxWalltime"
            :disabled="defaultQueueAttributesDisabled"
          ></b-form-input>
        </b-form-group>
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
        return this.data.compute_host_id.substring(0, 10) + "...";
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
            (q) => q.queue_name === this.data.default_queue_name
          )
        : null;
      return queue ? queue.max_nodes : 0;
    },
    maxCPUCount() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.default_queue_name
          )
        : null;
      return queue ? queue.max_processors : 0;
    },
    maxWalltime() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.default_queue_name
          )
        : null;
      return queue ? queue.max_run_time : 0;
    },
    cpuPerNode() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.default_queue_name
          )
        : null;
      return queue ? queue.cpu_per_node : 0;
    },
    defaultQueueAttributesDisabled() {
      return !this.data.default_queue_name || this.readonly;
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
        ? this.owner.first_name +
            " " +
            this.owner.last_name +
            " (" +
            this.owner.email +
            ")"
        : null;
    },
  },
  created() {
    services.ComputeResourceService.retrieve({
      lookup: this.data.compute_host_id,
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
        this.data.default_node_count = queue.default_node_count;
        this.data.default_cpu_count = queue.default_cpu_count;
        this.data.default_walltime = queue.default_walltime;
      } else {
        this.data.default_node_count = null;
        this.data.default_cpu_count = null;
        this.data.default_walltime = null;
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
