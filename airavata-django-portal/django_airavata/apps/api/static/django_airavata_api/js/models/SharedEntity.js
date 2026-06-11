import BaseModel from "./BaseModel";
import GroupPermission from "./GroupPermission";
import UserPermission from "./UserPermission";
import UserProfile from "./UserProfile";
import ResourcePermissionType from "./ResourcePermissionType";

const FIELDS = [
  "entity_id",
  {
    name: "user_permissions",
    type: UserPermission,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "group_permissions",
    type: GroupPermission,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "owner",
    type: UserProfile,
  },
  "is_owner",
  "has_sharing_permission",
];

export default class SharedEntity extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  addUser(user) {
    if (!this.user_permissions) {
      this.user_permissions = [];
    }
    if (
      !this.user_permissions.find(
        (up) =>
          up.user.airavata_internal_user_id === user.airavata_internal_user_id
      )
    ) {
      this.user_permissions.push(
        new UserPermission({
          user: user,
          permission_type: ResourcePermissionType.READ,
        })
      );
    }
  }

  removeUser(user) {
    this.user_permissions = this.user_permissions.filter(
      (userPermission) =>
        userPermission.user.airavata_internal_user_id !==
        user.airavata_internal_user_id
    );
  }

  addGroup({ group, permissionType = ResourcePermissionType.READ }) {
    if (!this.group_permissions) {
      this.group_permissions = [];
    }
    if (!this.group_permissions.find((gp) => gp.group.id === group.id)) {
      this.group_permissions.push(
        new GroupPermission({
          group: group,
          permission_type: permissionType,
        })
      );
    }
  }

  removeGroup(group) {
    this.group_permissions = this.group_permissions.filter(
      (groupPermission) => groupPermission.group.id !== group.id
    );
  }

  get nonAdminGroupPermissions() {
    if (this.group_permissions) {
      return this.group_permissions.filter(
        (groupPermission) => !groupPermission.group.isAdminGroup
      );
    } else {
      return [];
    }
  }
}
