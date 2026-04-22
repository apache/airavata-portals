import BaseModel from "./BaseModel";

const FIELDS = [
  "error_id",
  {
    name: "creation_time",
    type: "date",
  },
  "actualErrorMessage",
  "userFriendlyMessage",
  "transientOrPersistent",
  {
    name: "rootCauseErrorIdList",
    type: "string",
    list: true,
  },
];

export default class ErrorModel extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
