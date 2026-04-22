import BaseModel from "./BaseModel";
import ParserInputFile from "./ParserInput";
import ParserOutputFile from "./ParserOutput";

const FIELDS = [
  "id",
  "image_name",
  "output_dir_path",
  "input_dir_path",
  "execution_command",
  {
    name: "input_files",
    list: true,
    type: ParserInputFile,
  },
  {
    name: "output_files",
    list: true,
    type: ParserOutputFile,
  },
  "gateway_id",
];

export default class Parser extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
