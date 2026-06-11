import BaseModel from "./BaseModel";

// Wire shape is the file-service FileMetadataResponse rendered proto-direct, with
// user_has_write_access / is_shared_dir layered on by the view. The legacy
// `hidden` flag has no proto counterpart and is no longer on the wire.
const FIELDS = [
  "name",
  "path",
  {
    name: "created_time",
    type: "date",
  },
  {
    name: "modified_time",
    type: "date",
  },
  // int64 -> decimal string on the wire.
  "size",
  "is_directory",
  "content_type",
  "data_product_uri",
  "user_has_write_access",
  "is_shared_dir",
];

export default class UserStorageDirectory extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
