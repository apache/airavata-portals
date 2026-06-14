<template>
  <div class="space-y-1.5" v-if="localComputeResourcePolicy">
    <Label>Allowed Queues</Label>
    <div
      v-for="batchQueue in batchQueues"
      :key="batchQueue.queue_name"
      class="space-y-2"
    >
      <label class="flex items-center gap-2 text-sm">
        <Checkbox
          :model-value="
            localComputeResourcePolicy.allowed_batch_queues.includes(
              batchQueue.queue_name,
            )
          "
          :disabled="readonly"
          @update:model-value="batchQueueChecked(batchQueue, $event)"
        />
        {{ batchQueue.queue_name }}
      </label>
      <batch-queue-resource-policy
        v-if="
          localComputeResourcePolicy.allowed_batch_queues.includes(
            batchQueue.queue_name,
          )
        "
        :batch-queue="batchQueue"
        :readonly="readonly"
        :value="
          localBatchQueueResourcePolicies.find(
            (pol) => pol.queuename === batchQueue.queue_name,
          )
        "
        @input="updatedBatchQueueResourcePolicy(batchQueue, $event)"
        @valid="recordValidBatchQueueResourcePolicy(batchQueue)"
        @invalid="recordInvalidBatchQueueResourcePolicy(batchQueue)"
      />
    </div>
    <p
      v-if="validationFeedback.allowed_batch_queues.state === false"
      class="text-sm text-destructive"
    >
      {{ validationFeedback.allowed_batch_queues.invalidFeedback }}
    </p>
  </div>
</template>

<script>
import BatchQueueResourcePolicy from "./BatchQueueResourcePolicy.vue";

import { models } from "django-airavata-api";
import { errors } from "django-airavata-common-ui";

export default {
  name: "compute-resource-policy-editor",
  props: {
    batchQueues: {
      type: Array,
    },
    computeResourcePolicy: {
      type: models.ComputeResourcePolicy,
    },
    batchQueueResourcePolicies: {
      type: Array,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  components: {
    BatchQueueResourcePolicy,
  },
  data: function () {
    return {
      localComputeResourcePolicy: this.computeResourcePolicy
        ? this.computeResourcePolicy.clone()
        : null,
      localBatchQueueResourcePolicies: this.batchQueueResourcePolicies
        ? this.batchQueueResourcePolicies.map((pol) => pol.clone())
        : [],
      validationErrors: null,
      invalidBatchQueueResourcePolicies: [],
    };
  },
  computed: {
    computeResourcePolicyValidation() {
      return this.localComputeResourcePolicy.validate();
    },
    validationFeedback() {
      return errors.ValidationErrors.createValidationFeedback(
        this.localComputeResourcePolicy,
        this.computeResourcePolicyValidation,
      );
    },
    valid() {
      return (
        this.allowedInvalidBatchQueueResourcePolicies.length === 0 &&
        Object.keys(this.computeResourcePolicyValidation).length === 0
      );
    },
    allowedInvalidBatchQueueResourcePolicies() {
      return this.invalidBatchQueueResourcePolicies.filter((queueName) =>
        this.localComputeResourcePolicy.allowed_batch_queues.includes(
          queueName,
        ),
      );
    },
  },
  methods: {
    batchQueueChecked: function (batchQueue, checked) {
      if (checked) {
        this.localComputeResourcePolicy.allowed_batch_queues.push(
          batchQueue.queue_name,
        );
      } else {
        const queueIndex =
          this.localComputeResourcePolicy.allowed_batch_queues.indexOf(
            batchQueue.queue_name,
          );
        this.localComputeResourcePolicy.allowed_batch_queues.splice(
          queueIndex,
          1,
        );
        // Remove batchQueueResourcePolicy if it exists
        const policyIndex = this.localBatchQueueResourcePolicies.findIndex(
          (pol) => pol.queuename === batchQueue.queue_name,
        );
        if (policyIndex >= 0) {
          this.localBatchQueueResourcePolicies.splice(policyIndex, 1);
        }
        this.$emit(
          "batch-queue-resource-policies-updated",
          this.localBatchQueueResourcePolicies,
        );
      }
      this.validate();
      this.$emit(
        "compute-resource-policy-updated",
        this.localComputeResourcePolicy,
      );
    },
    updatedBatchQueueResourcePolicy: function (
      batchQueue,
      batchQueueResourcePolicy,
    ) {
      const queueName = batchQueue.queue_name;
      if (batchQueueResourcePolicy) {
        const existingPolicy = this.localBatchQueueResourcePolicies.find(
          (pol) => pol.queuename === queueName,
        );
        if (existingPolicy) {
          Object.assign(existingPolicy, batchQueueResourcePolicy);
        } else {
          this.localComputeResourcePolicy.populateParentIdsOnBatchQueueResourcePolicy(
            batchQueueResourcePolicy,
          );
          this.localBatchQueueResourcePolicies.push(batchQueueResourcePolicy);
        }
      } else {
        const existingPolicyIndex =
          this.localBatchQueueResourcePolicies.findIndex(
            (pol) => pol.queuename === queueName,
          );
        if (existingPolicyIndex >= 0) {
          this.localBatchQueueResourcePolicies.splice(existingPolicyIndex, 1);
        }
      }
      this.$emit(
        "batch-queue-resource-policies-updated",
        this.localBatchQueueResourcePolicies,
      );
    },
    recordValidBatchQueueResourcePolicy(batchQueue) {
      if (
        this.invalidBatchQueueResourcePolicies.includes(batchQueue.queue_name)
      ) {
        const index = this.invalidBatchQueueResourcePolicies.indexOf(
          batchQueue.queue_name,
        );
        this.invalidBatchQueueResourcePolicies.splice(index, 1);
      }
      this.validate(); // propagate validation
    },
    recordInvalidBatchQueueResourcePolicy(batchQueue) {
      if (
        !this.invalidBatchQueueResourcePolicies.includes(batchQueue.queue_name)
      ) {
        this.invalidBatchQueueResourcePolicies.push(batchQueue.queue_name);
      }
      this.validate(); // propagate validation
    },
    validate() {
      if (this.valid) {
        this.$emit("valid");
      } else {
        this.$emit("invalid");
      }
    },
  },
  watch: {
    computeResourcePolicy(value) {
      this.localComputeResourcePolicy = value.clone();
    },
    batchQueueResourcePolicies(value) {
      this.localBatchQueueResourcePolicies = value
        ? value.map((p) => p.clone())
        : [];
    },
  },
};
</script>

<style></style>
