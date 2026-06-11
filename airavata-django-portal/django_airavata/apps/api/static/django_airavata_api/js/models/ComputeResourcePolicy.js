import BaseModel from "./BaseModel";

const FIELDS = [
  "resource_policy_id",
  "compute_resource_id",
  "group_resource_profile_id",
  {
    name: "allowed_batch_queues",
    type: "string",
    list: true,
  },
];

export default class ComputeResourcePolicy extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  populateParentIdsOnBatchQueueResourcePolicy(batchQueueResourcePolicy) {
    // For new BatchQueueResourcePolicy instances, set the parent ids
    batchQueueResourcePolicy.group_resource_profile_id = this.group_resource_profile_id;
    batchQueueResourcePolicy.compute_resource_id = this.compute_resource_id;
    return batchQueueResourcePolicy;
  }

  validate() {
    let validationResults = {};
    if (!this.allowed_batch_queues || this.allowed_batch_queues.length === 0) {
      validationResults["allowed_batch_queues"] =
        "Must select at least one queue.";
    }
    return validationResults;
  }
}
