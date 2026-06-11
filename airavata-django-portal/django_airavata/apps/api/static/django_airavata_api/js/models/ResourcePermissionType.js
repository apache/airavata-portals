import BaseEnum from "./BaseEnum";

export default class ResourcePermissionType extends BaseEnum {}
ResourcePermissionType.init([
  "RESOURCE_PERMISSION_TYPE_UNKNOWN",
  "WRITE",
  "READ",
  "OWNER",
  "MANAGE_SHARING",
]);
