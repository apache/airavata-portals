import BaseModel from "./BaseModel";
import Group from "./Group";

const FIELDS = [
  "airavata_internal_user_id",
  "user_id",
  "gateway_id",
  "email",
  "first_name",
  "last_name",
  "enabled",
  "email_verified",
  {
    name: "creation_time",
    type: "date",
  },
  "airavata_user_profile_exists",
  // merged onto the proto server-side by the WithAccess envelope.
  "user_has_write_access",
  {
    name: "groups",
    type: Group,
    list: true,
  },
  "external_idp_user_info",
  "user_profile_invalid_fields",
];

export default class IAMUserProfile extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
  get userProfileComplete() {
    return this.user_profile_invalid_fields.length === 0;
  }
}
