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
        {
          name: "permission_type",
          type: ResourcePermissionType,
        },
      ],
      data
    );
  }
}
