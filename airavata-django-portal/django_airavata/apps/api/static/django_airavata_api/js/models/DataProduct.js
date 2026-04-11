import BaseModel from "./BaseModel";
import DataReplicaLocation from "./DataReplicaLocation";

import URL from "url-parse";

const FIELDS = [
  "product_uri",
  "gateway_id",
  "parent_product_uri",
  "product_name",
  "product_description",
  "owner_name",
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
  "product_metadata",
  {
    name: "replica_locations",
    type: DataReplicaLocation,
    list: true,
  },
  "download_url",
  "is_input_file_upload",
  "filesize",
  "user_has_write_access",
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
      const firstReplicaLocation = this.replica_locations[0];
      const fileURL = new URL(firstReplicaLocation.filePath);
      const filenameMatch = FILENAME_REGEX.exec(fileURL.pathname);
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
