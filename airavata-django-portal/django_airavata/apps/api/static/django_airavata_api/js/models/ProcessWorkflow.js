import BaseModel from "./BaseModel";

const FIELDS = [
  "process_id",
  "workflow_id",
  {
    name: "creation_time",
    type: "date",
  },
  "type",
];

export default class ProcessWorkflow extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
