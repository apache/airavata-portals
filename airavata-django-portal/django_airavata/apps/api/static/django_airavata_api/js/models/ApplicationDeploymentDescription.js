import BaseModel from "./BaseModel";
import ParallelismType from "./ParallelismType";
import CommandObject from "./CommandObject";
import SetEnvPaths from "./SetEnvPaths";

const FIELDS = [
  "app_deployment_id",
  "app_module_id",
  "compute_host_id",
  "executable_path",
  {
    name: "parallelism",
    type: ParallelismType,
    default: ParallelismType.SERIAL,
  },
  "app_deployment_description",
  {
    name: "module_load_cmds",
    type: CommandObject,
    list: true,
  },
  {
    name: "lib_prepend_paths",
    type: SetEnvPaths,
    list: true,
  },
  {
    name: "lib_append_paths",
    type: SetEnvPaths,
    list: true,
  },
  {
    name: "set_environment",
    type: SetEnvPaths,
    list: true,
  },
  {
    name: "pre_job_commands",
    type: CommandObject,
    list: true,
  },
  {
    name: "post_job_commands",
    type: CommandObject,
    list: true,
  },
  "default_queue_name",
  "default_node_count",
  "default_cpu_count",
  "default_walltime",
  {
    name: "editable_by_user",
    type: "boolean",
    default: false,
  },
  // WithAccess-merged scalar (not on the proto).
  "user_has_write_access",
];

export default class ApplicationDeploymentDescription extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
