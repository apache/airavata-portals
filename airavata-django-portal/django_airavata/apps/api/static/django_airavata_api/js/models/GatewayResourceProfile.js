import BaseModel from "./BaseModel";
import StoragePreference from "./StoragePreference";

const FIELDS = [
  "gateway_id",
  "credential_store_token",
  "compute_resource_preferences",
  {
    name: "storage_preferences",
    type: StoragePreference,
    list: true,
  },
  "identity_server_tenant",
  "identity_server_pwd_cred_token",
  "user_has_write_access",
];

export default class GatewayResourceProfile extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
