import BaseModel from "./BaseModel";
import uuidv4 from "uuid/v4";

const FIELDS = ["name", "value", "env_path_order"];

export default class SetEnvPaths extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
    this._key = data.key ? data.key : uuidv4();
  }

  get key() {
    return this._key;
  }
}
