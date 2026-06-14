<template>
  <div>
    <div>
      <h2 class="mb-1 text-lg font-semibold">
        {{ name }}
      </h2>
      <p v-if="owner" class="mb-2 text-muted-foreground">
        Created by <span :title="ownerTitle">{{ ownerUserId }}</span>
      </p>
      <share-button
        class="mt-2 mb-2"
        v-if="localSharedEntity"
        :shared-entity="localSharedEntity"
        @saved="savedSharedEntity"
        @unsaved="unsavedSharedEntity"
      />
      <div class="space-y-4">
        <div class="space-y-1.5">
          <Label for="executable-path">Application Executable Path</Label>
          <Input
            id="executable-path"
            type="text"
            v-model="data.executable_path"
            required
            :disabled="readonly"
          ></Input>
        </div>
        <div class="space-y-1.5">
          <Label for="parallelism-type">Application Parallelism Type</Label>
          <select
            id="parallelism-type"
            v-model="data.parallelism"
            :disabled="readonly"
            class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option
              v-for="opt in parallelismTypeOptions"
              :key="opt.text"
              :value="opt.value"
            >
              {{ opt.text }}
            </option>
          </select>
        </div>
        <div class="space-y-1.5">
          <Label for="deployment-description"
            >Application Deployment Description</Label
          >
          <Textarea
            id="deployment-description"
            v-model="data.app_deployment_description"
            :rows="3"
            :disabled="readonly"
          ></Textarea>
        </div>
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
        <div class="space-y-1.5">
          <Label for="default-queue-name">Default Queue Name</Label>
          <select
            id="default-queue-name"
            v-model="data.default_queue_name"
            @change="defaultQueueChanged($event.target.value)"
            :disabled="readonly"
            class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option :value="null">Select a Default Queue</option>
            <option
              v-for="opt in queueNameOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.text }}
            </option>
          </select>
        </div>
        <div class="space-y-1.5">
          <Label for="default-node-count">Default Node Count</Label>
          <Input
            id="default-node-count"
            type="number"
            v-model="data.default_node_count"
            min="0"
            :max="maxNodes"
            :disabled="defaultQueueAttributesDisabled"
          ></Input>
        </div>
        <div class="space-y-1.5">
          <Label for="default-cpu-count">Default CPU Count</Label>
          <Input
            id="default-cpu-count"
            type="number"
            v-model="data.default_cpu_count"
            min="0"
            :max="maxCPUCount"
            :disabled="defaultQueueAttributesDisabled"
          ></Input>
          <p v-if="cpuPerNode > 0" class="text-sm text-muted-foreground">
            There are {{ cpuPerNode }} cores per node.
          </p>
        </div>
        <div class="space-y-1.5">
          <Label for="default-walltime">Default Walltime (in minutes)</Label>
          <Input
            id="default-walltime"
            type="number"
            v-model="data.default_walltime"
            min="0"
            :max="maxWalltime"
            :disabled="defaultQueueAttributesDisabled"
          ></Input>
        </div>
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
            (q) => q.queue_name === this.data.default_queue_name,
          )
        : null;
      return queue ? queue.max_nodes : 0;
    },
    maxCPUCount() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.default_queue_name,
          )
        : null;
      return queue ? queue.max_processors : 0;
    },
    maxWalltime() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.default_queue_name,
          )
        : null;
      return queue ? queue.max_run_time : 0;
    },
    cpuPerNode() {
      const queue = this.computeResource
        ? this.computeResource.batch_queues.find(
            (q) => q.queue_name === this.data.default_queue_name,
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
          (q) => q.queue_name === queueName,
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
    // Vue 3 removed component $on/$off; replaces the previous
    // mounted `$on("input", () => this.dirty = true)` self-listener by marking
    // the editor dirty whenever the bound model changes.
    data: {
      handler() {
        this.dirty = true;
      },
      deep: true,
    },
  },
};
</script>
