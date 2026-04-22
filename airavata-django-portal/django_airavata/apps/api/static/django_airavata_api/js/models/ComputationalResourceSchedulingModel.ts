import BaseModel from "./BaseModel";

const FIELDS = [
  "resource_host_id",
  "total_cpu_count",
  "node_count",
  "number_of_threads",
  "queue_name",
  "wall_time_limit",
  "total_physical_memory",
  "chessis_number",
  "static_working_dir",
  "override_login_user_name",
  "override_scratch_location",
  "override_allocation_project_number",
];

export default class ComputationalResourceSchedulingModel extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  validate(queueInfo: Record<string, unknown> | null = null, batchQueueResourcePolicy: Record<string, unknown> | null = null) {
    const validationResults: Record<string, string> = {};
    if (this.isEmpty(this.resource_host_id)) {
      validationResults["resource_host_id"] = "Please select a compute resource.";
    }
    if (this.isEmpty(this.queue_name)) {
      validationResults["queue_name"] = "Please select a queue.";
    }
    if (!(this.node_count as number > 0)) {
      validationResults["node_count"] = "Enter a node count greater than 0.";
    } else if (
      batchQueueResourcePolicy &&
      (this.node_count as number) > (batchQueueResourcePolicy.max_allowed_nodes as number)
    ) {
      validationResults["node_count"] =
        `Enter a node count no greater than ${batchQueueResourcePolicy.max_allowed_nodes}.`;
    } else if (queueInfo && queueInfo.max_nodes && (this.node_count as number) > (queueInfo.max_nodes as number)) {
      validationResults["node_count"] =
        `Enter a node count no greater than ${queueInfo.max_nodes}.`;
    }
    if (!(this.total_cpu_count as number > 0)) {
      validationResults["total_cpu_count"] = "Enter a core count greater than 0.";
    } else if (
      batchQueueResourcePolicy &&
      (this.total_cpu_count as number) > (batchQueueResourcePolicy.max_allowed_cores as number)
    ) {
      validationResults["total_cpu_count"] =
        `Enter a core count no greater than ${batchQueueResourcePolicy.max_allowed_cores}.`;
    } else if (
      queueInfo &&
      queueInfo.max_processors &&
      (this.total_cpu_count as number) > (queueInfo.max_processors as number)
    ) {
      validationResults["total_cpu_count"] =
        `Enter a core count no greater than ${queueInfo.max_processors}.`;
    }
    if (!(this.wall_time_limit as number > 0)) {
      validationResults["wall_time_limit"] = "Enter a wall time limit greater than 0.";
    } else if (
      batchQueueResourcePolicy &&
      (this.wall_time_limit as number) > (batchQueueResourcePolicy.max_allowed_walltime as number)
    ) {
      validationResults["wall_time_limit"] =
        `Enter a wall time limit no greater than ${batchQueueResourcePolicy.max_allowed_walltime}.`;
    } else if (
      queueInfo &&
      queueInfo.max_run_time &&
      (this.wall_time_limit as number) > (queueInfo.max_run_time as number)
    ) {
      validationResults["wall_time_limit"] =
        `Enter a wall time limit no greater than ${queueInfo.max_run_time}.`;
    }
    if (!((this.total_physical_memory as number) >= 0)) {
      validationResults["total_physical_memory"] =
        "Enter a total physical memory greater than or equal to 0.";
    } else if (
      queueInfo &&
      queueInfo.max_memory &&
      (this.total_physical_memory as number) > (queueInfo.max_memory as number)
    ) {
      validationResults["total_physical_memory"] =
        `Enter a total physical memory no greater than ${queueInfo.max_memory}.`;
    }
    return validationResults;
  }
}
