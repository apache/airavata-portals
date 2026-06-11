import BaseModel from "./BaseModel";
import JobState from "./JobState";

const FIELDS = [
  {
    name: "job_state",
    type: JobState,
  },
  {
    name: "time_of_state_change",
    type: "date",
  },
  "reason",
  "status_id",
];

export default class JobStatus extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
