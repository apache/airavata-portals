import BaseModel from "./BaseModel";

const FIELDS = [
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
  "user_has_write_access",
];

export default class UnverifiedEmailUserProfile extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
