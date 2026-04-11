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
  constructor(data = {}) {
    super(FIELDS, data);
  }

  validate(queueInfo = null, batchQueueResourcePolicy = null) {
    const validationResults = {};
    if (this.isEmpty(this.resource_host_id)) {
      validationResults["resource_host_id"] = "Please select a compute resource.";
    }
    if (this.isEmpty(this.queue_name)) {
      validationResults["queue_name"] = "Please select a queue.";
    }
    if (!(this.node_count > 0)) {
      validationResults["node_count"] = "Enter a node count greater than 0.";
    } else if (
      batchQueueResourcePolicy &&
      this.node_count > batchQueueResourcePolicy.maxAllowedNodes
    ) {
      validationResults[
        "node_count"
      ] = `Enter a node count no greater than ${batchQueueResourcePolicy.maxAllowedNodes}.`;
    } else if (
      queueInfo &&
      queueInfo.maxNodes &&
      this.node_count > queueInfo.maxNodes
    ) {
      validationResults[
        "node_count"
      ] = `Enter a node count no greater than ${queueInfo.maxNodes}.`;
    }
    if (!(this.total_cpu_count > 0)) {
      validationResults["total_cpu_count"] = "Enter a core count greater than 0.";
    } else if (
      batchQueueResourcePolicy &&
      this.total_cpu_count > batchQueueResourcePolicy.maxAllowedCores
    ) {
      validationResults[
        "total_cpu_count"
      ] = `Enter a core count no greater than ${batchQueueResourcePolicy.maxAllowedCores}.`;
    } else if (
      queueInfo &&
      queueInfo.maxProcessors &&
      this.total_cpu_count > queueInfo.maxProcessors
    ) {
      validationResults[
        "total_cpu_count"
      ] = `Enter a core count no greater than ${queueInfo.maxProcessors}.`;
    }
    if (!(this.wall_time_limit > 0)) {
      validationResults["wall_time_limit"] =
        "Enter a wall time limit greater than 0.";
    } else if (
      batchQueueResourcePolicy &&
      this.wall_time_limit > batchQueueResourcePolicy.maxAllowedWalltime
    ) {
      validationResults[
        "wall_time_limit"
      ] = `Enter a wall time limit no greater than ${batchQueueResourcePolicy.maxAllowedWalltime}.`;
    } else if (
      queueInfo &&
      queueInfo.maxRunTime &&
      this.wall_time_limit > queueInfo.maxRunTime
    ) {
      validationResults[
        "wall_time_limit"
      ] = `Enter a wall time limit no greater than ${queueInfo.maxRunTime}.`;
    }
    if (!(this.total_physical_memory >= 0)) {
      validationResults["total_physical_memory"] =
        "Enter a total physical memory greater than or equal to 0.";
    } else if (
      queueInfo &&
      queueInfo.maxMemory &&
      this.total_physical_memory > queueInfo.maxMemory
    ) {
      validationResults[
        "total_physical_memory"
      ] = `Enter a total physical memory no greater than ${queueInfo.maxMemory}.`;
    }
    return validationResults;
  }
}
