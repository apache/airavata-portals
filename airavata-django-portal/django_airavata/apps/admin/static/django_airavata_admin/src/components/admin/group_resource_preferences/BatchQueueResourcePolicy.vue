<template>
  <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
    <div class="space-y-1.5">
      <Label for="max-allowed-nodes">Maximum Allowed Nodes</Label>
      <Input
        id="max-allowed-nodes"
        type="number"
        v-model="data.max_allowed_nodes"
        :readonly="readonly"
        @input="policyUpdated"
        min="1"
        :max="batchQueue.max_nodes"
        :placeholder="'Max Nodes: ' + batchQueue.max_nodes"
        :aria-invalid="validationFeedback.max_allowed_nodes.state === false"
      >
      </Input>
      <p
        v-if="validationFeedback.max_allowed_nodes.state === false"
        class="text-sm text-destructive"
      >
        {{ validationFeedback.max_allowed_nodes.invalidFeedback }}
      </p>
    </div>
    <div class="space-y-1.5">
      <Label for="max-allowed-cores">Maximum Allowed Cores</Label>
      <Input
        id="max-allowed-cores"
        type="number"
        v-model="data.max_allowed_cores"
        :readonly="readonly"
        @input="policyUpdated"
        min="1"
        :max="batchQueue.max_processors"
        :placeholder="'Max Cores: ' + batchQueue.max_processors"
        :aria-invalid="validationFeedback.max_allowed_cores.state === false"
      >
      </Input>
      <p
        v-if="validationFeedback.max_allowed_cores.state === false"
        class="text-sm text-destructive"
      >
        {{ validationFeedback.max_allowed_cores.invalidFeedback }}
      </p>
    </div>
    <div class="space-y-1.5">
      <Label for="max-allowed-walltime">Maximum Allowed Wall Time</Label>
      <Input
        id="max-allowed-walltime"
        type="number"
        v-model="data.max_allowed_walltime"
        :readonly="readonly"
        @input="policyUpdated"
        min="1"
        :max="batchQueue.max_run_time"
        :placeholder="'Max Wall Time: ' + batchQueue.max_run_time"
        :aria-invalid="validationFeedback.max_allowed_walltime.state === false"
      >
      </Input>
      <p
        v-if="validationFeedback.max_allowed_walltime.state === false"
        class="text-sm text-destructive"
      >
        {{ validationFeedback.max_allowed_walltime.invalidFeedback }}
      </p>
    </div>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { errors as uiErrors } from "django-airavata-common-ui";

export default {
  name: "batch-queue-resource-policy",
  props: {
    value: {
      required: false,
      type: models.BatchQueueResourcePolicy,
    },
    batchQueue: {
      required: true,
      type: models.BatchQueue,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  created() {
    this.validate();
  },
  watch: {
    // Vue 3 removed component $on; replaces `this.$on("input", this.validate)`
    // self-listener by re-validating whenever the local model changes.
    data: {
      handler() {
        this.validate();
      },
      deep: true,
    },
  },
  data: function () {
    const localValue = this.value
      ? this.value.clone()
      : new models.BatchQueueResourcePolicy();
    localValue.queuename = this.batchQueue.queue_name;
    return {
      data: localValue,
    };
  },
  methods: {
    policyUpdated: function () {
      if (
        this.data.max_allowed_nodes ||
        this.data.max_allowed_cores ||
        this.data.max_allowed_walltime
      ) {
        this.$emit("input", this.data);
      } else {
        this.$emit("input", null);
      }
    },
    numberFormatter: function (value) {
      const num = parseInt(value);
      return !isNaN(num) ? "" + num : value;
    },
    validate() {
      if (this.valid) {
        this.$emit("valid");
      } else {
        this.$emit("invalid");
      }
    },
  },
  computed: {
    valid() {
      return Object.keys(this.validation).length === 0;
    },
    validation() {
      return this.data.validate(this.batchQueue);
    },
    validationFeedback() {
      return uiErrors.ValidationErrors.createValidationFeedback(
        this.data,
        this.validation,
      );
    },
  },
};
</script>
