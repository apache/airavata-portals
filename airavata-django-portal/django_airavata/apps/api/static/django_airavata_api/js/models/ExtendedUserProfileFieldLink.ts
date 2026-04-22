import BaseModel from "./BaseModel";
import { v4 as uuidv4 } from "uuid";

const FIELDS = ["id", "label", "url", "order", "display_link", "display_inline"];

export default class ExtendedUserProfileFieldLink extends BaseModel {
  [key: string]: unknown;
  private _key: string;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
    this._key = data.key ? (data.key as string) : uuidv4();
  }

  get key() {
    return this._key;
  }

  toJSON() {
    const copy = Object.assign({}, this) as Record<string, unknown>;
    // id must either have a value or be missing, it can't be null
    if (!copy.id) {
      delete copy.id;
    }
    return copy;
  }
}
