import BaseModel from "./BaseModel";
import BatchQueue from "./BatchQueue";

const FIELDS = [
  "compute_resource_id",
  "host_name",
  {
    name: "host_aliases",
    type: "string",
    list: true,
  },
  {
    name: "ip_addresses",
    type: "string",
    list: true,
  },
  "resource_description",
  "enabled",
  {
    name: "batch_queues",
    type: BatchQueue,
    list: true,
  },
  // TODO: map these
  // 'file_systems',
  // 'job_submission_interfaces',
  // 'data_movement_interfaces',
  "max_memory_per_node",
  "gateway_usage_reporting",
  "gateway_usage_module_load_command",
  "gateway_usage_executable",
  "cpus_per_node",
  "default_node_count",
  "default_cpu_count",
  "default_walltime",
];

export default class ComputeResourceDescription extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
