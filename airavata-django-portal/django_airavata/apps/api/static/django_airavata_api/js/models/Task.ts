import BaseModel from "./BaseModel";
import ErrorModel from "./ErrorModel";
import Job from "./Job";
import TaskTypes from "./TaskTypes";
import TaskStatus from "./TaskStatus";

const FIELDS = [
  "task_id",
  {
    name: "task_type",
    type: TaskTypes,
  },
  "parent_process_id",
  {
    name: "creation_time",
    type: Date,
  },
  {
    name: "last_update_time",
    type: Date,
  },
  {
    name: "task_statuses",
    type: TaskStatus,
    list: true,
  },
  "task_detail",
  "sub_task_model",
  {
    name: "task_errors",
    type: ErrorModel,
    list: true,
  },
  {
    name: "jobs",
    type: Job,
    list: true,
  },
  "max_retry",
  "current_retry",
];

export default class Task extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  get latestStatus() {
    if (this.task_statuses && (this.task_statuses as TaskStatus[]).length > 0) {
      return (this.task_statuses as TaskStatus[])[(this.task_statuses as TaskStatus[]).length - 1];
    } else {
      return null;
    }
  }
}
