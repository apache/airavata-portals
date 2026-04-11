import BaseModel from "./BaseModel";

const FIELDS = [
  "process_id",
  "workflow_id",
  {
    name: "creation_time",
    type: Date,
  },
  "type",
];

export default class ProcessWorkflow extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
