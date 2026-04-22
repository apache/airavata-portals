import BaseEnum from "./BaseEnum";

export default class TaskTypes extends BaseEnum {
  static ENV_SETUP: TaskTypes;
  static DATA_STAGING: TaskTypes;
  static JOB_SUBMISSION: TaskTypes;
  static ENV_CLEANUP: TaskTypes;
  static MONITORING: TaskTypes;
  static OUTPUT_FETCHING: TaskTypes;
  static values: TaskTypes[];
}
TaskTypes.init([
  "ENV_SETUP",
  "DATA_STAGING",
  "JOB_SUBMISSION",
  "ENV_CLEANUP",
  "MONITORING",
  "OUTPUT_FETCHING",
]);
