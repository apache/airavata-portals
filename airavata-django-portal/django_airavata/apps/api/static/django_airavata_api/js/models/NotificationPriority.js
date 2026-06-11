import BaseEnum from "./BaseEnum";

export default class NotificationPriority extends BaseEnum {}
// writeName: serializes the proto member name on the wire (LOW/NORMAL/HIGH are
// bare proto names; the 0-sentinel keeps its NOTIFICATION_PRIORITY_ prefix).
NotificationPriority.init(
  ["NOTIFICATION_PRIORITY_UNKNOWN", "LOW", "NORMAL", "HIGH"],
  true
);
