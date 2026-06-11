import BaseModel from "./BaseModel";
import UserStorageDirectory from "./UserStorageDirectory";
import UserStorageFile from "./UserStorageFile";

// Not a single proto message: the UserStoragePathView assembles this from a
// list_dir response (files/directories as proto-direct FileMetadataResponse) plus
// view-synthesized is_dir / parts / path / user_has_write_access scalars.
const FIELDS = [
  {
    name: "files",
    type: UserStorageFile,
    list: true,
  },
  {
    name: "directories",
    type: UserStorageDirectory,
    list: true,
  },
  {
    name: "parts",
    type: "string",
    list: true,
  },
  "path",
  {
    name: "is_dir",
    type: "boolean",
    list: false,
  },
  {
    name: "user_has_write_access",
    type: "boolean",
    default: true,
  },
];

export default class UserStoragePath extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
