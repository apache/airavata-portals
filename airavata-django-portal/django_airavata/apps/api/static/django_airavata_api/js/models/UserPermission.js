import BaseModel from "./BaseModel";
import ResourcePermissionType from "./ResourcePermissionType";
import UserProfile from "./UserProfile";

export default class UserPermission extends BaseModel {
  constructor(data = {}) {
    super(
      [
        {
          name: "user",
          type: UserProfile,
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
