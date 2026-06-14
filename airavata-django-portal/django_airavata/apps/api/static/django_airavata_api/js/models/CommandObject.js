import BaseModel from "./BaseModel";

const FIELDS = ["command", "command_order"];

export default class CommandObject extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
    this._key = data.key ? data.key : crypto.randomUUID();
  }

  get key() {
    return this._key;
  }
}
