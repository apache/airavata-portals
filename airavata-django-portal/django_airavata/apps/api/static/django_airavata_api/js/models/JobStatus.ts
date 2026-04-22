import BaseModel from "./BaseModel";
import JobState from "./JobState";

const FIELDS = [
  {
    name: "jobState",
    type: JobState,
  },
  {
    name: "timeOfStateChange",
    type: "date",
  },
  "reason",
  "statusId",
];

export default class JobStatus extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
