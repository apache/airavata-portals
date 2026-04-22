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
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
