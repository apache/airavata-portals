import BaseModel from "./BaseModel";

const FIELDS = [
  "resource_policy_id",
  "compute_resource_id",
  "group_resource_profile_id",
  "queuename",
  "max_allowed_nodes",
  "max_allowed_cores",
  "max_allowed_walltime",
];

export default class BatchQueueResourcePolicy extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  validate(batchQueue) {
    let validationResults = {};
    if (this.max_allowed_nodes && this.max_allowed_nodes < 1) {
      validationResults["max_allowed_nodes"] = "Must be at least 1.";
    } else if (this.max_allowed_nodes > batchQueue.max_nodes) {
      validationResults[
        "max_allowed_nodes"
      ] = `Must be at most ${batchQueue.max_nodes}.`;
    }
    if (this.max_allowed_cores && this.max_allowed_cores < 1) {
      validationResults["max_allowed_cores"] = "Must be at least 1.";
    } else if (this.max_allowed_cores > batchQueue.max_processors) {
      validationResults[
        "max_allowed_cores"
      ] = `Must be at most ${batchQueue.max_processors}.`;
    }
    if (this.max_allowed_walltime && this.max_allowed_walltime < 1) {
      validationResults["max_allowed_walltime"] = "Must be at least 1.";
    } else if (this.max_allowed_walltime > batchQueue.max_run_time) {
      validationResults[
        "max_allowed_walltime"
      ] = `Must be at most ${batchQueue.max_run_time}.`;
    }
    return validationResults;
  }
}
