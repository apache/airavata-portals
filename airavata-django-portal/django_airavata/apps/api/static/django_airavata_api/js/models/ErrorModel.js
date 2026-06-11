import BaseModel from "./BaseModel";

const FIELDS = [
  "error_id",
  {
    name: "creation_time",
    type: "date",
  },
  "actual_error_message",
  "user_friendly_message",
  "transient_or_persistent",
  {
    name: "root_cause_error_id_list",
    type: "string",
    list: true,
  },
];

export default class ErrorModel extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
