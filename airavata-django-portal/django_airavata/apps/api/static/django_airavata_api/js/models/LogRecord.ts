import BaseModel from "./BaseModel";

const FIELDS = [
  "level",
  "message",
  "details",
  {
    name: "stacktrace",
    type: "string",
    list: true,
  },
];

export default class LogRecord extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
