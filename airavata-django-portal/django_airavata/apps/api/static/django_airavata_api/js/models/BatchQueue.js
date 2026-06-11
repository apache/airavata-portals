import BaseModel from "./BaseModel";

const FIELDS = [
  "queue_name",
  "queue_description",
  "max_run_time",
  "max_nodes",
  "max_processors",
  "max_jobs_in_queue",
  "max_memory",
  "cpu_per_node",
  "default_node_count",
  "default_cpu_count",
  "default_walltime",
  "queue_specific_macros",
  "is_default_queue",
];

export default class BatchQueue extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
