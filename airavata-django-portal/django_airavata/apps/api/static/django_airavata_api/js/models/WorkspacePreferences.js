import BaseModel from "./BaseModel";

const FIELDS = [
  "most_recent_project_id",
  "most_recent_compute_resource_id",
  "application_preferences",
];

export default class WorkspacePreferences extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
