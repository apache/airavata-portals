import BaseModel from "./BaseModel";
import ResourcePermissionType from "./ResourcePermissionType";
import UserProfile from "./UserProfile";

export default class UserPermission extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(
      [
        {
          name: "user",
          type: UserProfile,
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
