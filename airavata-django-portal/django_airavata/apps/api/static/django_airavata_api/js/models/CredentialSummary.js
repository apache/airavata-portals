import BaseModel from "./BaseModel";
import SummaryType from "./SummaryType";

const FIELDS = [
  {
    name: "type",
    type: SummaryType,
  },
  "gateway_id",
  "username",
  "public_key",
  {
    name: "persisted_time",
    type: "date",
  },
  "token",
  "description",
  // merged onto the proto server-side by the WithAccess envelope.
  "user_has_write_access",
];

export default class CredentialSummary extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
