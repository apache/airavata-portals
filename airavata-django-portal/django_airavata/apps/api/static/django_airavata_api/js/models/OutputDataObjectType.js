import BaseModel from "./BaseModel";
import DataType from "./DataType";
import { v4 as uuidv4 } from "uuid";
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
    return this.meta_data ? this.meta_data["file-metadata"] : null;
  }

  get fileMetadataMimeType() {
    return this.fileMetadata && this.fileMetadata["mime-type"]
      ? this.fileMetadata["mime-type"]
      : null;
  }
}

OutputDataObjectType.VALID_DATA_TYPES = DataType.values;
