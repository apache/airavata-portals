import BaseModel from "./BaseModel";
import ResourceType from "./ResourceType";
import SlurmComputeResourcePreference from "./SlurmComputeResourcePreference";
import AwsComputeResourcePreference from "./AwsComputeResourcePreference";

const FIELDS = [
  "compute_resource_id",
  "group_resource_profile_id",
  {
    name: "override_by_airavata",
    type: "boolean",
    default: true,
  },
  "login_user_name",
  // wire enum member NAMES ("SSH"/"SFTP"); sentinels *_PROTOCOL_UNKNOWN.
  "preferred_job_submission_protocol",
  "preferred_data_movement_protocol",
  "scratch_location",
  "resource_specific_credential_store_token",
  {
    name: "resource_type",
    type: ResourceType,
  },
  // oneof wrapper {slurm:{...}} | {aws:{...}}; coerced into a child model below.
  {
    name: "specific_preferences",
    type: null,
  },
];

const PREFERENCE_MODEL_MAP = {
  SLURM: SlurmComputeResourcePreference,
  AWS: AwsComputeResourcePreference,
};

export default class GroupComputeResourcePreference extends BaseModel {
  constructor(data = {}) {
    const rawSpecificPreferences = data.specific_preferences;

    super(FIELDS, data);

    if (rawSpecificPreferences !== undefined && rawSpecificPreferences !== null) {
      this.specific_preferences = rawSpecificPreferences;
    }

    this._coerceSpecificPreferences();
  }

  toJSON() {
    const json = { ...this };
    if (this.resource_type && this.resource_type.value !== undefined) {
      json.resource_type = this.resource_type.value;
    } else if (this.resource_type && this.resource_type.name) {
      json.resource_type = this.resource_type.name;
    }

    let specificPrefsPayload = this.specific_preferences;
    if (
      this.specific_preferences &&
      typeof this.specific_preferences.toJSON === "function"
    ) {
      specificPrefsPayload = this.specific_preferences.toJSON();
    }

    // re-wrap into the proto oneof shape the wire expects.
    if (specificPrefsPayload && this.isResourceType("SLURM")) {
      json.specific_preferences = { slurm: specificPrefsPayload };
    } else if (specificPrefsPayload && this.isResourceType("AWS")) {
      json.specific_preferences = { aws: specificPrefsPayload };
    } else if (specificPrefsPayload) {
      json.specific_preferences = specificPrefsPayload;
    } else {
      json.specific_preferences = null;
    }

    return json;
  }

  _coerceSpecificPreferences() {
    if (!this.resource_type) {
      this.specific_preferences = null;
      return;
    }

    if (!this.resource_type.name) {
      return;
    }

    if (
      this.specific_preferences &&
      this.specific_preferences instanceof BaseModel
    ) {
      return;
    }
    let rawData =
      this.specific_preferences && typeof this.specific_preferences === "object"
        ? this.specific_preferences
        : null;

    // unwrap the proto oneof wrapper ({slurm:{...}} / {aws:{...}}).
    if (rawData && !(rawData instanceof BaseModel)) {
      if (this.resource_type.name === "SLURM" && "slurm" in rawData) {
        rawData = rawData.slurm;
      } else if (this.resource_type.name === "AWS" && "aws" in rawData) {
        rawData = rawData.aws;
      }
    }

    const PreferenceModel = PREFERENCE_MODEL_MAP[this.resource_type.name];
    if (PreferenceModel) {
      const newPref = rawData
        ? new PreferenceModel(rawData)
        : new PreferenceModel();
      this.specific_preferences = newPref;
    } else {
      this.specific_preferences = rawData;
    }
  }

  resetSpecificPreferences(data = null) {
    if (!this.resource_type) {
      this.specific_preferences = null;
      return;
    }
    if (data && typeof data === "object") {
      this.specific_preferences = data;
    } else {
      this.specific_preferences = null;
    }
    this._coerceSpecificPreferences();
  }

  isResourceType(resourceTypeName) {
    return !!this.resource_type && this.resource_type.name === resourceTypeName;
  }

  _ensureSpecificPreferences() {
    if (!this.specific_preferences) {
      this._coerceSpecificPreferences();
    }
  }

  // SLURM-only convenience accessors bridging into the child preference model.
  _getSlurmField(fieldName, defaultValue) {
    if (this.isResourceType("SLURM") && this.specific_preferences) {
      return this.specific_preferences[fieldName];
    }
    return defaultValue;
  }

  _setSlurmField(fieldName, value) {
    if (!this.isResourceType("SLURM")) {
      return;
    }
    this._ensureSpecificPreferences();
    if (this.specific_preferences) {
      this.specific_preferences[fieldName] = value;
    }
  }

  get allocation_project_number() {
    return this._getSlurmField("allocation_project_number");
  }

  set allocation_project_number(value) {
    this._setSlurmField("allocation_project_number", value);
  }

  get preferred_batch_queue() {
    return this._getSlurmField("preferred_batch_queue");
  }

  set preferred_batch_queue(value) {
    this._setSlurmField("preferred_batch_queue", value);
  }

  get quality_of_service() {
    return this._getSlurmField("quality_of_service");
  }

  set quality_of_service(value) {
    this._setSlurmField("quality_of_service", value);
  }

  get usage_reporting_gateway_id() {
    return this._getSlurmField("usage_reporting_gateway_id");
  }

  set usage_reporting_gateway_id(value) {
    this._setSlurmField("usage_reporting_gateway_id", value);
  }

  get reservations() {
    return this._getSlurmField("reservations", []);
  }

  set reservations(value) {
    this._setSlurmField("reservations", value);
  }

  validate() {
    let validationResults = {};
    if (this.isEmpty(this.login_user_name)) {
      validationResults["login_user_name"] = "Please provide a login username.";
    }
    if (this.isEmpty(this.scratch_location)) {
      validationResults["scratch_location"] =
        "Please provide a scratch location.";
    }
    if (!this.resource_type) {
      validationResults["resource_type"] = "Please select a resource type.";
    }
    if (this.resource_type && this.specific_preferences) {
      const specificValidation = this.specific_preferences.validate();
      if (specificValidation && Object.keys(specificValidation).length > 0) {
        Object.assign(validationResults, specificValidation);
      }
    }
    return validationResults;
  }
}
