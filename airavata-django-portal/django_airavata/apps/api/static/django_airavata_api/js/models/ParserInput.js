import BaseModel from "./BaseModel";
import IOType from "./IOType";

const FIELDS = [
  "id",
  "name",
  "required_input",
  "parser_id",
  {
    name: "type",
    type: IOType,
  },
];

export default class ParserInput extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
