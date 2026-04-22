import BaseModel from "./BaseModel";
import BatchQueueResourcePolicy from "./BatchQueueResourcePolicy";
import ComputeResourcePolicy from "./ComputeResourcePolicy";
import GroupComputeResourcePreference from "./GroupComputeResourcePreference";

const FIELDS = [
  "gateway_id",
  "group_resource_profile_id",
  "group_resource_profile_name",
  {
    name: "compute_preferences",
    type: GroupComputeResourcePreference,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "compute_resource_policies",
    type: ComputeResourcePolicy,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "batch_queue_resource_policies",
    type: BatchQueueResourcePolicy,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "updated_time",
    type: "date",
  },
  "default_credential_store_token",
  "user_has_write_access", // true if current user has write access
];

export default class GroupResourceProfile extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  getComputePreference(computeResourceId: string) {
    return (this.compute_preferences as GroupComputeResourcePreference[]).find((pref) => pref.compute_resource_id === computeResourceId);
  }

  getComputeResourcePolicy(computeResourceId: string) {
    return (this.compute_resource_policies as ComputeResourcePolicy[]).find(
      (pol) => pol.compute_resource_id === computeResourceId,
    );
  }

  getBatchQueueResourcePolicies(computeResourceId: string) {
    return (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).filter(
      (pol) => pol.compute_resource_id === computeResourceId,
    );
  }

  mergeComputeResourcePreference(
    computeResourcePreference: GroupComputeResourcePreference,
    computeResourcePolicy: ComputeResourcePolicy,
    batchQueueResourcePolicies: BatchQueueResourcePolicy[],
  ) {
    // merge/add computeResourcePreference and computeResourcePolicy
    const existingComputeResourcePreference = (this.compute_preferences as GroupComputeResourcePreference[]).find(
      (pref) => pref.compute_resource_id === computeResourcePreference.compute_resource_id,
    );
    if (existingComputeResourcePreference) {
      Object.assign(existingComputeResourcePreference, computeResourcePreference);
    } else {
      (this.compute_preferences as GroupComputeResourcePreference[]).push(computeResourcePreference);
    }
    const existingComputeResourcePolicy = (this.compute_resource_policies as ComputeResourcePolicy[]).find(
      (pol) => pol.compute_resource_id === computeResourcePolicy.compute_resource_id,
    );
    if (existingComputeResourcePolicy) {
      Object.assign(existingComputeResourcePolicy, computeResourcePolicy);
    } else {
      (this.compute_resource_policies as ComputeResourcePolicy[]).push(computeResourcePolicy);
    }
    // merge/add/remove batchQueueResourcePolicies
    const existingBatchQueueResourcePolicies = (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).filter(
      (pol) => pol.compute_resource_id === computeResourcePreference.compute_resource_id,
    );
    for (const batchQueueResourcePolicy of batchQueueResourcePolicies) {
      const existingBatchQueueResourcePolicy = existingBatchQueueResourcePolicies.find(
        (pol) => pol.queuename === batchQueueResourcePolicy.queuename,
      );
      if (existingBatchQueueResourcePolicy) {
        Object.assign(existingBatchQueueResourcePolicy, batchQueueResourcePolicy);
        const existingBatchQueueResourcePolicyIndex = existingBatchQueueResourcePolicies.findIndex(
          (pol) => pol.queuename === batchQueueResourcePolicy.queuename,
        );
        if (existingBatchQueueResourcePolicyIndex >= 0) {
          existingBatchQueueResourcePolicies.splice(existingBatchQueueResourcePolicyIndex, 1);
        }
      } else {
        (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).push(batchQueueResourcePolicy);
      }
    }
    for (const existingBatchQueueResourcePolicy of existingBatchQueueResourcePolicies) {
      const existingBatchQueueResourcePolicyIndex = (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).findIndex(
        (pol) =>
          pol.compute_resource_id === existingBatchQueueResourcePolicy.compute_resource_id &&
          pol.queuename === existingBatchQueueResourcePolicy.queuename,
      );
      if (existingBatchQueueResourcePolicyIndex >= 0) {
        (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).splice(existingBatchQueueResourcePolicyIndex, 1);
      }
    }
  }

  /**
   * Remove compute resource preference, compute resource policy and batch queue policies.
   * @param {string} computeResourceId
   * @returns {boolean} true if this GroupResourceProfile was changed
   */
  removeComputeResource(computeResourceId: string) {
    let removedChildren = false;
    const existingComputeResourcePreferenceIndex = (this.compute_preferences as GroupComputeResourcePreference[]).findIndex(
      (pref) => pref.compute_resource_id === computeResourceId,
    );
    if (existingComputeResourcePreferenceIndex >= 0) {
      (this.compute_preferences as GroupComputeResourcePreference[]).splice(existingComputeResourcePreferenceIndex, 1);
      removedChildren = true;
    }
    const existingComputeResourcePolicyIndex = (this.compute_resource_policies as ComputeResourcePolicy[]).findIndex(
      (pol) => pol.compute_resource_id === computeResourceId,
    );
    if (existingComputeResourcePolicyIndex >= 0) {
      (this.compute_resource_policies as ComputeResourcePolicy[]).splice(existingComputeResourcePolicyIndex, 1);
      removedChildren = true;
    }
    const existingBatchQueueResourcePolicies = (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).filter(
      (pol) => pol.compute_resource_id === computeResourceId,
    );
    for (const existingBatchQueueResourcePolicy of existingBatchQueueResourcePolicies) {
      const existingBatchQueueResourcePolicyIndex = (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).indexOf(
        existingBatchQueueResourcePolicy,
      );
      (this.batch_queue_resource_policies as BatchQueueResourcePolicy[]).splice(existingBatchQueueResourcePolicyIndex, 1);
      removedChildren = true;
    }

    return removedChildren;
  }
}
