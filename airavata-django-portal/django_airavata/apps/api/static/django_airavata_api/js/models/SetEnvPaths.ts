import BaseModel from "./BaseModel";
import { v4 as uuidv4 } from "uuid";

const FIELDS = ["name", "value", "env_path_order"];

export default class SetEnvPaths extends BaseModel {
  [key: string]: unknown;
  private _key: string;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
    this._key = data.key ? (data.key as string) : uuidv4();
  }

  get key() {
    return this._key;
  }
}
