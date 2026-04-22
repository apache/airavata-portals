import BaseModel from "./BaseModel";

const FIELDS = ["region", "preferred_ami_id", "preferred_instance_type"];

export default class AwsComputeResourcePreference extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  toJSON() {
    return { ...this };
  }

  validate() {
    return {};
  }
}
