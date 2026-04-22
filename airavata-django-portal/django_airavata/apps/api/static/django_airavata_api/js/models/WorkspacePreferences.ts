import BaseModel from "./BaseModel";

const FIELDS = [
  "most_recent_project_id",
  "most_recent_compute_resource_id",
  "application_preferences",
];

export default class WorkspacePreferences extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }
}
