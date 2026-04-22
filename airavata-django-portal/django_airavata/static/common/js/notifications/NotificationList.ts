import Notification from "./Notification";

class NotificationList {
  private notifications: Notification[];

  constructor() {
    this.notifications = [];
  }

  add(notification: Notification): void {
    this.notifications.push(notification);
  }

  // Convenience method for adding an error
  addError(error: { message: string }): void {
    this.notifications.push(
      new Notification({
        type: "ERROR",
        message: error.message,
      })
    );
  }

  remove(notification: Notification): void {
    const i = this.notifications.indexOf(notification);
    this.notifications.splice(i, 1);
  }

  get list(): Notification[] {
    return this.notifications;
  }
}

export default new NotificationList();
