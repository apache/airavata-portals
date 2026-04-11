import BaseModel from "./BaseModel";

const FIELDS = [
  "app_module_id",
  "app_module_name",
  "app_module_version",
  "app_module_description",
  "user_has_write_access",
];

export default class ApplicationModule extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
