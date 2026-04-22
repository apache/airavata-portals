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
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  addUser(user: UserProfile) {
    if (!this.user_permissions) {
      this.user_permissions = [];
    }
    if (
      !(this.user_permissions as UserPermission[]).find(
        (up) => (up.user as UserProfile).airavata_internal_user_id === user.airavata_internal_user_id,
      )
    ) {
      (this.user_permissions as UserPermission[]).push(
        new UserPermission({
          user: user,
          permission_type: ResourcePermissionType.READ,
        }),
      );
    }
  }

  removeUser(user: UserProfile) {
    this.user_permissions = (this.user_permissions as UserPermission[]).filter(
      (userPermission) =>
        (userPermission.user as UserProfile).airavata_internal_user_id !== user.airavata_internal_user_id,
    );
  }

  addGroup({ group, permissionType = ResourcePermissionType.READ }: { group: Record<string, unknown>; permissionType?: ResourcePermissionType }) {
    if (!this.group_permissions) {
      this.group_permissions = [];
    }
    if (!(this.group_permissions as GroupPermission[]).find((gp) => (gp.group as Record<string, unknown>).id === group.id)) {
      (this.group_permissions as GroupPermission[]).push(
        new GroupPermission({
          group: group,
          permission_type: permissionType,
        }),
      );
    }
  }

  removeGroup(group: Record<string, unknown>) {
    this.group_permissions = (this.group_permissions as GroupPermission[]).filter(
      (groupPermission) => (groupPermission.group as Record<string, unknown>).id !== group.id,
    );
  }

  get nonAdminGroupPermissions() {
    if (this.group_permissions) {
      return (this.group_permissions as GroupPermission[]).filter(
        (groupPermission) => !(groupPermission.group as { isAdminGroup: boolean }).isAdminGroup,
      );
    } else {
      return [];
    }
  }
}
