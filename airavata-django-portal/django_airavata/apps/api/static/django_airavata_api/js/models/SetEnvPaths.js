import BaseModel from "./BaseModel";

const FIELDS = ["name", "value", "env_path_order"];

export default class SetEnvPaths extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
    this._key = data.key ? data.key : crypto.randomUUID();
  }

  get key() {
    return this._key;
  }
}
