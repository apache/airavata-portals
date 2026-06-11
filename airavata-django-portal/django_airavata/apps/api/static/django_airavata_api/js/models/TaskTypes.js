import BaseEnum from "./BaseEnum";

export default class TaskTypes extends BaseEnum {}
TaskTypes.init([
  "TASK_TYPES_UNKNOWN",
  "ENV_SETUP",
  "DATA_STAGING",
  "JOB_SUBMISSION",
  "ENV_CLEANUP",
  "MONITORING",
  "OUTPUT_FETCHING",
]);
