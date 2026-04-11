import BaseModel from "./BaseModel";

const FIELDS = [
  "name",
  "download_url",
  "data_product_uri",
  { name: "created_time", type: "date" },
  { name: "modified_time", type: "date" },
  "size",
  "mime_type",
  "user_has_write_access",
];

export default class UserStorageFile extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
