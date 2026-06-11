import BaseModel from "./BaseModel";

// Wire shape is the file-service FileMetadataResponse rendered proto-direct,
// with user_has_write_access layered on by the view. The legacy downloadURL was
// view-synthesized and is no longer on the wire.
const FIELDS = [
  "name",
  "path",
  "data_product_uri",
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
  "user_has_write_access",
];

export default class UserStorageFile extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
