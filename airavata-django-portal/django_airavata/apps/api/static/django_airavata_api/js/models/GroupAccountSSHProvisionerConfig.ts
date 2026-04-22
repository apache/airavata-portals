import BaseModel from "./BaseModel";

const FIELDS = ["resource_id", "group_resource_profile_id", "config_name", "config_value"];

export default class GroupAccountSSHProvisionerConfig extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  toJSON() {
    return { ...this };
  }
}
