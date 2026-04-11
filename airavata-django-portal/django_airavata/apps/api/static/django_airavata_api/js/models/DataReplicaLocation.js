import BaseModel from "./BaseModel";

const FIELDS = [
  "replica_id",
  "product_uri",
  "replica_name",
  "replica_description",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "last_modified_time",
    type: "date",
  },
  {
    name: "valid_until_time",
    type: "date",
  },
  "replica_location_category",
  "replica_persistent_type",
  "storage_resource_id",
  "file_path",
  "replica_metadata",
];

export default class DataReplicaLocation extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
