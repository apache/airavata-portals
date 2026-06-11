import BaseModel from "./BaseModel";
import TaskState from "./TaskState";

const FIELDS = [
  {
    name: "state",
    type: TaskState,
  },
  {
    name: "time_of_state_change",
    type: "date",
  },
  "reason",
  "status_id",
];

export default class TaskStatus extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
