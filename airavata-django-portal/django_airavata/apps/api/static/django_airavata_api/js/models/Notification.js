import BaseModel from "./BaseModel";
import NotificationPriority from "./NotificationPriority";

const FIELDS = [
  "notification_id",
  "gateway_id",
  "title",
  "notification_message",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "published_time",
    type: "date",
  },
  {
    name: "expiration_time",
    type: "date",
  },
  {
    name: "priority",
    type: NotificationPriority,
  },
  // WithAccess-merged scalars (not proto fields).
  "user_has_write_access",
  "is_owner",
  // Portal-only NotificationExtension flag, merged on top of the proto.
  {
    name: "show_in_dashboard",
    type: "boolean",
    default: false,
  },
];

export default class Notification extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  validate() {
    let validationResults = {};
    if (this.isEmpty(this.title)) {
      validationResults["title"] = "Please provide a Title for this notice.";
    }
    if (
      this.isEmpty(this.notification_message) ||
      this.notification_message.length < 10
    ) {
      validationResults["notification_message"] =
        "Please provide the message with minimum 10 characters.";
    }
    if (this.isEmpty(this.published_time)) {
      validationResults["published_time"] = "Please select the publish time";
    }
    if (this.isEmpty(this.expiration_time)) {
      validationResults["expiration_time"] = "Please select the expiration time";
    }
    if (this.isEmpty(this.priority)) {
      validationResults["priority"] = "Please select the priority";
    }
    return validationResults;
  }
}
