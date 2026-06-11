import BaseModel from "./BaseModel";
import Group from "./Group";
import ResourcePermissionType from "./ResourcePermissionType";

export default class GroupPermission extends BaseModel {
  constructor(data = {}) {
    super(
      [
        {
          name: "group",
          type: Group,
        },
        // permission_type arrives as the enum member NAME string.
        {
          name: "permission_type",
          type: ResourcePermissionType,
        },
      ],
      data
    );
  }
}
