import BaseModel from "./BaseModel";

const FIELDS = ["fileUploadMaxFileSize", "tusEndpoint", "pgaUrl"];

export default class Settings extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
