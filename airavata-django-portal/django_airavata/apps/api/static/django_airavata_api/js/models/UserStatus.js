import BaseEnum from "./BaseEnum";

// Proto enum is `Status` (prefix STATUS_), not UserStatus; members below are the
// bare proto names, so they register as-is. The STATUS_UNKNOWN sentinel registers
// only under its full name (the class-derived USER_STATUS_ prefix doesn't strip it).
export default class UserStatus extends BaseEnum {}
UserStatus.init([
  "STATUS_UNKNOWN",
  "ACTIVE",
  "CONFIRMED",
  "APPROVED",
  "DELETED",
  "DUPLICATE",
  "GRACE_PERIOD",
  "INVITED",
  "DENIED",
  "PENDING",
  "PENDING_APPROVAL",
  "PENDING_CONFIRMATION",
  "SUSPENDED",
  "DECLINED",
  "EXPIRED",
]);
