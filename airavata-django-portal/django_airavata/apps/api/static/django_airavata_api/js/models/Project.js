import BaseModel from "./BaseModel";

const FIELDS = [
  "project_id",
  "owner",
  "gateway_id",
  "name",
  "description",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "shared_users",
    type: "string",
    list: true,
  },
  {
    name: "shared_groups",
    type: "string",
    list: true,
  },
  // merged onto the proto server-side by the WithAccess envelope.
  "is_owner",
  {
    name: "user_has_write_access",
    type: "boolean",
    default: true,
  },
];

export default class Project extends BaseModel {
  constructor(data = {}) {
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
