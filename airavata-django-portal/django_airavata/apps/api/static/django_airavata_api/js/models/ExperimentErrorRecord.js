import BaseModel from "./BaseModel";

const FIELDS = [
  "id",
  "experimentId",
  "username",
  "level",
  "message",
  "details",
  "stacktrace",
  "count",
  {
    name: "created",
    type: Date,
  },
  {
    name: "updated",
    type: Date,
  },
];

export default class ExperimentErrorRecord extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
