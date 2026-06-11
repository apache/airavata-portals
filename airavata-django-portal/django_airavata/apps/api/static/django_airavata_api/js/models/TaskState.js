import BaseEnum from "./BaseEnum";

export default class TaskState extends BaseEnum {}
TaskState.init([
  "TASK_STATE_UNKNOWN",
  "TASK_STATE_CREATED",
  "TASK_STATE_EXECUTING",
  "TASK_STATE_COMPLETED",
  "TASK_STATE_FAILED",
  "TASK_STATE_CANCELED",
]);
