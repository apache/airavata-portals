<template>
  <ul>
    <li v-for="queuePolicy in queuePolicies" :key="queuePolicy.name">
      {{ queuePolicy.name }}
      <template v-if="queuePolicy.policy">
        (<span title="Max Allowed Nodes"
          >N:
          {{
            queuePolicy.policy.max_allowed_nodes
              ? queuePolicy.policy.max_allowed_nodes
              : "Unlimited"
          }}</span
        >,
        <span title="Max Allowed Cores"
          >C:
          {{
            queuePolicy.policy.max_allowed_cores
              ? queuePolicy.policy.max_allowed_cores
              : "Unlimited"
          }}</span
        >,
        <span title="Max Allowed Walltime"
          >W:
          {{
            queuePolicy.policy.max_allowed_walltime
              ? queuePolicy.policy.max_allowed_walltime
              : "Unlimited"
          }}</span
        >)
      </template>
    </li>
  </ul>
</template>

<script>
import { models } from "django-airavata-api";

export default {
  name: "compute-resource-policy-summary",
  props: {
    computeResourceId: {
      type: String,
      required: true,
    },
    groupResourceProfile: {
      type: models.GroupResourceProfile,
    },
  },
  computed: {
    queues: function () {
      const computeResourcePolicy = this.groupResourceProfile.getComputeResourcePolicy(
        this.computeResourceId
      );
      if (computeResourcePolicy && computeResourcePolicy.allowed_batch_queues) {
        const queues = computeResourcePolicy.allowed_batch_queues.slice();
        queues.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
        return queues;
      } else {
        return [];
      }
    },
    queuePolicies: function () {
      const result = [];
      for (const queue of this.queues) {
        const batchQueueResourcePolicies = this.groupResourceProfile.getBatchQueueResourcePolicies(
          this.computeResourceId
        );
        const batchQueueResourcePolicy = batchQueueResourcePolicies.find(
          (pol) => pol.queuename === queue
        );
        result.push({
          name: queue,
          policy: batchQueueResourcePolicy,
        });
      }
      return result;
    },
  },
};
</script>

<style scoped>
ul {
  padding-left: 20px;
}
</style>
