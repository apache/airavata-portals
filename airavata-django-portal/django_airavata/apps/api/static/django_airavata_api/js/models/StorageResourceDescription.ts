import BaseModel from "./BaseModel";

const FIELDS = [
  "storage_resource_id",
  "host_name",
  "storage_resource_description",
  "enabled",
  "data_movement_interfaces",
  "creation_time",
  "update_time",
];

export default class StorageResourceDescription extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
