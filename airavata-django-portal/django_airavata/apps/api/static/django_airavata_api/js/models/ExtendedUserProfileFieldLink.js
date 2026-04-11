import BaseModel from "./BaseModel";
import { v4 as uuidv4 } from "uuid";

const FIELDS = [
  "id",
  "label",
  "url",
  "order",
  "display_link",
  "display_inline",
];

export default class ExtendedUserProfileFieldLink extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
    this._key = data.key ? data.key : uuidv4();
  }

  get key() {
    return this._key;
  }

  toJSON() {
    const copy = Object.assign({}, this);
    // id must either have a value or be missing, it can't be null
    if (!copy.id) {
      delete copy.id;
    }
    return copy;
  }
}
