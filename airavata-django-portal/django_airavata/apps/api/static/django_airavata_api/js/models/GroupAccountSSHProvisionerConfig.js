import BaseModel from "./BaseModel";

const FIELDS = [
  "resource_id",
  "group_resource_profile_id",
  "config_name",
  "config_value",
];

export default class GroupAccountSSHProvisionerConfig extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  toJSON() {
    return { ...this };
  }
}
