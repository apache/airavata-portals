import BaseModel from "./BaseModel";
import DataType from "./DataType";
import uuidv4 from "uuid/v4";
import IntermediateOutput from "./IntermediateOutput";

const FIELDS = [
  "name",
  "value",
  {
    name: "type",
    type: DataType,
    default: DataType.URI,
  },
  "application_argument",
  {
    name: "is_required",
    type: "boolean",
    default: false,
  },
  {
    name: "required_to_added_to_command_line",
    type: "boolean",
    default: false,
  },
  {
    name: "data_movement",
    type: "boolean",
    default: false,
  },
  "location",
  "search_query",
  {
    name: "output_streaming",
    type: "boolean",
    default: false,
  },
  "storage_resource_id",
  "meta_data",
  // Not a proto field: the experiments ViewSet layers this snake_case block
  // (process_status + data_products + can_fetch) onto EXECUTING-state outputs.
  {
    name: "intermediate_output",
    type: IntermediateOutput,
  },
];

export default class OutputDataObjectType extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
    // Copy key when cloning a model
    this._key = data.key ? data.key : uuidv4();
  }

  get key() {
    return this._key;
  }

  get fileMetadata() {
    // Proto-direct: meta_data is a raw JSON string; parse before indexing.
    const metadata = this._getMetadata();
    return metadata ? metadata["file-metadata"] : null;
  }

  get fileMetadataMimeType() {
    return this.fileMetadata && this.fileMetadata["mime-type"]
      ? this.fileMetadata["mime-type"]
      : null;
  }

  _getMetadata() {
    if (!this.meta_data) {
      return null;
    }
    if (typeof this.meta_data === "object") {
      return this.meta_data;
    }
    if (typeof this.meta_data === "string") {
      try {
        const parsed = JSON.parse(this.meta_data);
        return typeof parsed === "object" ? parsed : null;
      } catch (e) {
        return null;
      }
    }
    return null;
  }
}

OutputDataObjectType.VALID_DATA_TYPES = DataType.values;
