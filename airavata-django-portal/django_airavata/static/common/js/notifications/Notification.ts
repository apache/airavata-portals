export type NotificationType = "SUCCESS" | "ERROR" | "WARNING" | "INFO";

export interface NotificationOptions {
  type?: NotificationType;
  message?: string | null;
  details?: unknown;
  dismissable?: boolean;
  duration?: number;
  createdDate?: Date | null;
}

let idSequence = 0;

class Notification {
  id: number;
  type: NotificationType;
  message: string | null;
  details: unknown;
  dismissable: boolean;
  duration: number;
  createdDate: Date;

  constructor({
    type = "SUCCESS",
    message = null,
    details = null,
    dismissable = true,
    duration = 0,
    createdDate = null,
  }: NotificationOptions = {}) {
    this.id = idSequence++;
    this.type = type;
    this.message = message;
    this.details = details;
    this.dismissable = dismissable;
    this.duration = duration;
    this.createdDate = createdDate ? createdDate : new Date();
  }
}

export default Notification;
