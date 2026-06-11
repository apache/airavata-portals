import BaseModel from "./BaseModel";

const FIELDS = [
  "storage_resource_id",
  "host_name",
  "storage_resource_description",
  "enabled",
  "data_movement_interfaces",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "update_time",
    type: "date",
  },
];

export default class StorageResourceDescription extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
