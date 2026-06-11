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
  // merged onto the proto server-side by the WithAccess envelope.
  "user_has_write_access",
];

export default class UnverifiedEmailUserProfile extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
