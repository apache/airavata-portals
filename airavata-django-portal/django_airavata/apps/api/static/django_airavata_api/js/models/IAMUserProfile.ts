import BaseModel from "./BaseModel";
import Group from "./Group";

const FIELDS = [
  "user_model_version",
  "airavata_internal_user_id",
  "user_id",
  "gateway_id",
  "email",
  "first_name",
  "last_name",
  "enabled",
  "email_verified",
  "airavata_user_profile_exists",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "groups",
    type: Group,
    list: true,
  },
  "user_has_write_access",
  "external_idp_user_info",
  "user_profile_invalid_fields",
];

export default class IAMUserProfile extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
  get userProfileComplete() {
    return (this.user_profile_invalid_fields as unknown[]).length === 0;
  }
}
