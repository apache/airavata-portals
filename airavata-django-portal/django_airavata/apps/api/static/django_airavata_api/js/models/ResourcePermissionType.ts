import BaseEnum from "./BaseEnum";

export default class ResourcePermissionType extends BaseEnum {
  static WRITE: ResourcePermissionType;
  static READ: ResourcePermissionType;
  static OWNER: ResourcePermissionType;
  static MANAGE_SHARING: ResourcePermissionType;
  static values: ResourcePermissionType[];
}
ResourcePermissionType.init(["WRITE", "READ", "OWNER", "MANAGE_SHARING"]);
