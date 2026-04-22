import BaseModel from "./BaseModel";

const FIELDS = ["id", "name"];

export default class QueueSettingsCalculator extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
