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
    type: Date,
  },
  "token",
  "description",
  "user_has_write_access",
];

export default class CredentialSummary extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
