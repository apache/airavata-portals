<template>
  <div class="row">
    <div class="col">
      <b-form-group
        label="Maximum Allowed Nodes"
        label-for="max-allowed-nodes"
        :invalid-feedback="validationFeedback.max_allowed_nodes.invalidFeedback"
        :state="validationFeedback.max_allowed_nodes.state"
      >
        <b-form-input
          id="max-allowed-nodes"
          type="number"
          v-model="data.max_allowed_nodes"
          :readonly="readonly"
          @input="policyUpdated"
          min="1"
          :max="batchQueue.max_nodes"
          :formatter="numberFormatter"
          :placeholder="'Max Nodes: ' + batchQueue.max_nodes"
          :state="validationFeedback.max_allowed_nodes.state"
        >
        </b-form-input>
      </b-form-group>
    </div>
    <div class="col">
      <b-form-group
        label="Maximum Allowed Cores"
        label-for="max-allowed-cores"
        :invalid-feedback="validationFeedback.max_allowed_cores.invalidFeedback"
        :state="validationFeedback.max_allowed_cores.state"
      >
        <b-form-input
          id="max-allowed-cores"
          type="number"
          v-model="data.max_allowed_cores"
          :readonly="readonly"
          @input="policyUpdated"
          min="1"
          :max="batchQueue.max_processors"
          :formatter="numberFormatter"
          :placeholder="'Max Cores: ' + batchQueue.max_processors"
          :state="validationFeedback.max_allowed_cores.state"
        >
        </b-form-input>
      </b-form-group>
    </div>
    <div class="col">
      <b-form-group
        label="Maximum Allowed Wall Time"
        label-for="max-allowed-walltime"
        :invalid-feedback="
          validationFeedback.max_allowed_walltime.invalidFeedback
        "
        :state="validationFeedback.max_allowed_walltime.state"
      >
        <b-form-input
          id="max-allowed-walltime"
          type="number"
          v-model="data.max_allowed_walltime"
          :readonly="readonly"
          @input="policyUpdated"
          min="1"
          :max="batchQueue.max_run_time"
          :formatter="numberFormatter"
          :placeholder="'Max Wall Time: ' + batchQueue.max_run_time"
          :state="validationFeedback.max_allowed_walltime.state"
        >
        </b-form-input>
      </b-form-group>
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
    readonly:{
      type: Boolean,
      default: false,
    },
  },
  created() {
    this.$on("input", this.validate);
    this.validate();
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
        this.validation
      );
    },
  },
};
</script>
