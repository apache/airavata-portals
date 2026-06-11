import BaseModel from "./BaseModel";
import IOType from "./IOType";

const FIELDS = [
  "id",
  "name",
  "required_output",
  "parser_id",
  {
    name: "type",
    type: IOType,
  },
];

export default class ParserOutput extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
