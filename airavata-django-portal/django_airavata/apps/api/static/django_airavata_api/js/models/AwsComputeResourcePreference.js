import BaseModel from "./BaseModel";

const FIELDS = [
  "region",
  "preferred_ami_id",
  "preferred_instance_type",
];

export default class AwsComputeResourcePreference extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  toJSON() {
    return { ...this };
  }

  validate() {
    return {};
  }
}
