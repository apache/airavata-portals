import BaseModel from "./BaseModel";
import NotificationPriority from "./NotificationPriority";

const FIELDS = [
  "notification_id",
  "gateway_id",
  "title",
  "notification_message",
  {
    name: "creation_time",
    type: Date,
  },
  {
    name: "published_time",
    type: Date,
  },
  {
    name: "expiration_time",
    type: Date,
  },
  {
    name: "priority",
    type: NotificationPriority,
  },
  "user_has_write_access",
  {
    name: "show_in_dashboard",
    type: "boolean",
    default: false,
  },
];

export default class Notification extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  validate() {
    const validationResults: Record<string, string> = {};
    if (this.isEmpty(this.title)) {
      validationResults["title"] = "Please provide a Title for this notice.";
    }
    if (this.isEmpty(this.notification_message) || (this.notification_message as string).length < 10) {
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
