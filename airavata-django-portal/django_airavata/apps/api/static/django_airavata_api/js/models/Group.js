import BaseModel from "./BaseModel";

const FIELDS = [
  "id",
  "name",
  "owner_id",
  "description",
  {
    name: "members",
    type: "string",
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "admins",
    type: "string",
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  // The six access flags are merged onto the GroupModel proto server-side by the
  // WithGroupAccess envelope (not on the proto itself).
  {
    name: "is_owner",
    type: "boolean",
    default: true,
  },
  {
    name: "is_admin",
    type: "boolean",
    default: false,
  },
  {
    name: "is_member",
    type: "boolean",
    default: true,
  },
  "is_gateway_admins_group",
  "is_read_only_gateway_admins_group",
  "is_default_gateway_users_group",
];

export default class Group extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  validate() {
    if (this.isEmpty(this.name.trim())) {
      return {
        name: ["Please provide a name."],
      };
    }
    return null;
  }

  /**
   * Return true if group is either the "Gateway Admins" or the "Readonly Admins" group.
   */
  get isAdminGroup() {
    return this.is_read_only_gateway_admins_group || this.is_gateway_admins_group;
  }

  get userHasWriteAccess() {
    return this.is_owner || this.is_admin;
  }
}
