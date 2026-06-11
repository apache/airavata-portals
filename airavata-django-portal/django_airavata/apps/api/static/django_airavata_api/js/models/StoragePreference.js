import BaseModel from "./BaseModel";

const FIELDS = [
  "storage_resource_id",
  "login_user_name",
  "file_system_root_location",
  "resource_specific_credential_store_token",
];

export default class StoragePreference extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
