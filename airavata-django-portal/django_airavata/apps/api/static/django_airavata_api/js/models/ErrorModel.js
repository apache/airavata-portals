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
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
