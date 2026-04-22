import BaseEnum from "./BaseEnum";

export default class UserStatus extends BaseEnum {
  static ACTIVE: UserStatus;
  static CONFIRMED: UserStatus;
  static APPROVED: UserStatus;
  static DELETED: UserStatus;
  static DUPLICATE: UserStatus;
  static GRACE_PERIOD: UserStatus;
  static INVITED: UserStatus;
  static DENIED: UserStatus;
  static PENDING: UserStatus;
  static PENDING_APPROVAL: UserStatus;
  static PENDING_CONFIRMATION: UserStatus;
  static SUSPENDED: UserStatus;
  static DECLINED: UserStatus;
  static EXPIRED: UserStatus;
  static values: UserStatus[];
}
UserStatus.init([
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
