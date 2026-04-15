import BaseModel from "./BaseModel";

const FIELDS = [
  "job_submission_interface_id",
  "job_submission_protocol",
  {
    name: "priority_order",
    type: "number",
    default: 0,
  },
];

export default class JobSubmissionInterface extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
