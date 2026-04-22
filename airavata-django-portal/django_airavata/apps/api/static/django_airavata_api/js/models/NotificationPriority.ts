import BaseEnum from "./BaseEnum";

export default class NotificationPriority extends BaseEnum {
  static LOW: NotificationPriority;
  static NORMAL: NotificationPriority;
  static HIGH: NotificationPriority;
  static values: NotificationPriority[];
}
NotificationPriority.init(["LOW", "NORMAL", "HIGH"], true);
