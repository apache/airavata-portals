import BaseModel from "./BaseModel";
import Group from "./Group";
import ResourcePermissionType from "./ResourcePermissionType";

export default class GroupPermission extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(
      [
        {
          name: "group",
          type: Group,
        },
        {
          name: "permission_type",
          type: ResourcePermissionType,
        },
      ],
      data,
    );
  }
}
