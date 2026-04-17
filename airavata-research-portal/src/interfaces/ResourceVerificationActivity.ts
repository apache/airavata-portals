import { Resource } from "./ResourceType";
import { StatusEnum } from "./StatusEnum";

export interface ResourceVerificationActivity {
  /**
   * The unique identifier for the activity, generated as a UUID.
   */
  id: string;

  /**
   * The resource associated with this verification activity.
   * Note: The @JsonBackReference in the backend means this property
   * might be excluded from the JSON to prevent circular dependencies.
   * If so, you might want to make this optional (e.g., `resource?: Resource`).
   */
  resource?: Resource;

  /**
   * The ID of the user who performed the activity (e.g., an admin or author).
   */
  userId: string;

  /**
   * The status of the verification activity.
   */
  status: StatusEnum;

  /**
   * An optional message associated with the activity, like a reason for rejection.
   */
  message?: string;

  /**
   * The timestamp when the record was created (ISO 8601 format).
   */
  createdAt: string;

  /**
   * The timestamp when the record was last updated (ISO 8601 format).
   */
  updatedAt: string;
}






