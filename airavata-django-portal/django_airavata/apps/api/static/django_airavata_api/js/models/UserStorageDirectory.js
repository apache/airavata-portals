import BaseModel from "./BaseModel";

const FIELDS = [
  "name",
  "path",
  { name: "created_time", type: "date" },
  { name: "modified_time", type: "date" },
  "size",
  "hidden",
  "user_has_write_access",
  "is_shared_dir",
];

export default class UserStorageDirectory extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
