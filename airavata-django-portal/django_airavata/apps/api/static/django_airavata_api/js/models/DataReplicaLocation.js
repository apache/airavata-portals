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
  // wire enum NAMEs ("GATEWAY_DATA_STORE" / "TRANSIENT"); 0-sentinels are
  // "REPLICA_LOCATION_CATEGORY_UNKNOWN" / "REPLICA_PERSISTENT_TYPE_UNKNOWN".
  "replica_location_category",
  "replica_persistent_type",
  "storage_resource_id",
  "file_path",
  // proto map<string,string>, arrives as a JSON object.
  "replica_metadata",
];

export default class DataReplicaLocation extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
