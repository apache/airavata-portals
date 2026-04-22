import BaseModel from "./BaseModel";
import TaskState from "./TaskState";

const FIELDS = [
  {
    name: "state",
    type: TaskState,
  },
  {
    name: "time_of_state_change",
    type: Date,
  },
  "reason",
  "status_id",
];

export default class TaskStatus extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
