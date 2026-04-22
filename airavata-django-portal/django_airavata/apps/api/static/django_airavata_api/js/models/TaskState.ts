import BaseEnum from "./BaseEnum";

export default class TaskState extends BaseEnum {
  static CREATED: TaskState;
  static EXECUTING: TaskState;
  static COMPLETED: TaskState;
  static FAILED: TaskState;
  static CANCELED: TaskState;
  static values: TaskState[];
}
TaskState.init(["CREATED", "EXECUTING", "COMPLETED", "FAILED", "CANCELED"]);
