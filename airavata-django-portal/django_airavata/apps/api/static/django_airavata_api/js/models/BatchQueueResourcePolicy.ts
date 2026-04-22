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
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  validate(batchQueue?: Record<string, unknown>) {
    const validationResults: Record<string, string> = {};
    if (this.max_allowed_nodes && (this.max_allowed_nodes as number) < 1) {
      validationResults["max_allowed_nodes"] = "Must be at least 1.";
    } else if (batchQueue && (this.max_allowed_nodes as number) > (batchQueue.max_nodes as number)) {
      validationResults["max_allowed_nodes"] = `Must be at most ${batchQueue.max_nodes}.`;
    }
    if (this.max_allowed_cores && (this.max_allowed_cores as number) < 1) {
      validationResults["max_allowed_cores"] = "Must be at least 1.";
    } else if (batchQueue && (this.max_allowed_cores as number) > (batchQueue.max_processors as number)) {
      validationResults["max_allowed_cores"] = `Must be at most ${batchQueue.max_processors}.`;
    }
    if (this.max_allowed_walltime && (this.max_allowed_walltime as number) < 1) {
      validationResults["max_allowed_walltime"] = "Must be at least 1.";
    } else if (batchQueue && (this.max_allowed_walltime as number) > (batchQueue.max_run_time as number)) {
      validationResults["max_allowed_walltime"] = `Must be at most ${batchQueue.max_run_time}.`;
    }
    return validationResults;
  }
}
