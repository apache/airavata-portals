import BaseModel from "./BaseModel";

const FIELDS = [
  "project_id",
  "name",
  "description",
  "owner",
  "gateway_id",
  {
    name: "creation_time",
    type: "date",
  },
  "user_has_write_access",
  "is_owner",
];

export default class Project extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  validate() {
    if (this.isEmpty(this.name)) {
      return {
        name: ["Please provide a name."],
      };
    }
    return null;
  }
}
