import BaseModel from "./BaseModel";
import DataReplicaLocation from "./DataReplicaLocation";

const FIELDS = [
  "product_uri",
  "gateway_id",
  "parent_product_uri",
  "product_name",
  "product_description",
  "owner_name",
  // wire enum NAME ("FILE" / "COLLECTION"); 0-sentinel "DATA_PRODUCT_TYPE_UNKNOWN".
  "data_product_type",
  "product_size",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "last_modified_time",
    type: "date",
  },
  // proto map<string,string>, arrives as a JSON object (e.g. {"mime-type": ...}).
  "product_metadata",
  {
    name: "replica_locations",
    type: DataReplicaLocation,
    list: true,
  },
  // merged onto the proto server-side by the WithAccess envelope.
  "is_owner",
  {
    name: "user_has_write_access",
    type: "boolean",
    default: true,
  },
];

const FILENAME_REGEX = /[^/]+$/;
const TEXT_MIME_TYPE_REGEX = /^text\/.+/;
const IMAGE_MIME_TYPE_REGEX = /^image\/.+/;

export default class DataProduct extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  get filename() {
    if (this.replica_locations && this.replica_locations.length > 0) {
      // file_path is a file:// URI or plain path; the last path segment is the filename.
      const filenameMatch = FILENAME_REGEX.exec(this.replica_locations[0].file_path);
      if (filenameMatch) {
        return filenameMatch[0];
      }
    }
    return null;
  }

  get isText() {
    return this.mimeType && TEXT_MIME_TYPE_REGEX.test(this.mimeType);
  }

  get isImage() {
    return this.mimeType && IMAGE_MIME_TYPE_REGEX.test(this.mimeType);
  }

  get mimeType() {
    return this.product_metadata && this.product_metadata["mime-type"]
      ? this.product_metadata["mime-type"]
      : null;
  }
}
