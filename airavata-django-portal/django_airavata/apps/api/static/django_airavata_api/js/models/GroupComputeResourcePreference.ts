import BaseModel from "./BaseModel";
import ResourceType from "./ResourceType";
import SlurmComputeResourcePreference from "./SlurmComputeResourcePreference";
import AwsComputeResourcePreference from "./AwsComputeResourcePreference";

const FIELDS = [
  "compute_resource_id",
  "group_resource_profile_id",
  {
    name: "overrideby_airavata",
    type: "boolean",
    default: true,
  },
  "login_user_name",
  "preferred_job_submission_protocol",
  "preferred_data_movement_protocol",
  "scratch_location",
  "resource_specific_credential_store_token",
  {
    name: "resource_type",
    type: ResourceType,
    required: true,
  },
  {
    name: "specific_preferences",
    type: null,
  },
];

const PREFERENCE_MODEL_MAP: Record<string, typeof SlurmComputeResourcePreference | typeof AwsComputeResourcePreference> = {
  SLURM: SlurmComputeResourcePreference,
  AWS: AwsComputeResourcePreference,
};

export default class GroupComputeResourcePreference extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    const topLevelAllocationProjectNumber = data.allocation_project_number;
    const rawSpecificPreferences = data.specific_preferences;

    super(FIELDS, data);

    const specificPrefsToUse =
      rawSpecificPreferences !== undefined && rawSpecificPreferences !== null
        ? rawSpecificPreferences
        : data.specific_preferences !== undefined && data.specific_preferences !== null
          ? data.specific_preferences
          : null;

    if (specificPrefsToUse !== null) {
      this.specific_preferences = specificPrefsToUse;
    }

    if (this.resource_type && typeof this.resource_type === "number") {
      this.resource_type =
        ResourceType.values.find((rt) => rt.value === this.resource_type) || this.resource_type;
    }

    if (topLevelAllocationProjectNumber) {
      if (this.resource_type && (this.resource_type as ResourceType).name === "SLURM") {
        if (!this.specific_preferences) {
          this.specific_preferences = {};
        }
        if (
          typeof this.specific_preferences === "object" &&
          !(this.specific_preferences instanceof BaseModel)
        ) {
          if (!(this.specific_preferences as Record<string, unknown>).allocation_project_number) {
            (this.specific_preferences as Record<string, unknown>).allocation_project_number = topLevelAllocationProjectNumber;
          }
        }
      } else if (!this.resource_type && topLevelAllocationProjectNumber) {
        this.resource_type = ResourceType.SLURM;
        if (!this.specific_preferences) {
          this.specific_preferences = {};
        }
        if (
          typeof this.specific_preferences === "object" &&
          !(this.specific_preferences instanceof BaseModel)
        ) {
          if (!(this.specific_preferences as Record<string, unknown>).allocation_project_number) {
            (this.specific_preferences as Record<string, unknown>).allocation_project_number = topLevelAllocationProjectNumber;
          }
        }
      }
    }

    this._coerceSpecificPreferences();
  }

  toJSON() {
    const json = { ...this } as Record<string, unknown>;
    if (this.resource_type && (this.resource_type as ResourceType).value !== undefined) {
      json.resource_type = (this.resource_type as ResourceType).value;
    } else if (this.resource_type && (this.resource_type as ResourceType).name) {
      json.resource_type = (this.resource_type as ResourceType).name;
    }

    let specificPrefsPayload: unknown = this.specific_preferences;
    if (this.specific_preferences && typeof (this.specific_preferences as { toJSON?: () => unknown }).toJSON === "function") {
      specificPrefsPayload = (this.specific_preferences as { toJSON: () => unknown }).toJSON();
    }

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
    // Ensure resource_type is properly set
    if (this.resource_type && typeof this.resource_type === "number") {
      this.resource_type =
        ResourceType.byValue(this.resource_type as number) ||
        ResourceType.values.find((rt) => rt.value === this.resource_type) ||
        this.resource_type;
    }

    if (!this.resource_type) {
      this.specific_preferences = null;
      return;
    }

    if (!(this.resource_type as ResourceType).name) {
      return;
    }

    if (this.specific_preferences && this.specific_preferences instanceof BaseModel) {
      return;
    }
    let rawData: Record<string, unknown> | null =
      this.specific_preferences && typeof this.specific_preferences === "object"
        ? (this.specific_preferences as Record<string, unknown>)
        : null;

    if (rawData && !(rawData instanceof BaseModel)) {
      if ((this.resource_type as ResourceType).name === "SLURM" && "slurm" in rawData) {
        rawData = rawData.slurm as Record<string, unknown>;
      } else if ((this.resource_type as ResourceType).name === "AWS") {
        if ("aws" in rawData) {
          rawData = rawData.aws as Record<string, unknown>;
        }
      }
    }

    const PreferenceModel = PREFERENCE_MODEL_MAP[(this.resource_type as ResourceType).name];
    if (PreferenceModel) {
      const newPref = rawData ? new PreferenceModel(rawData) : new PreferenceModel();
      this.specific_preferences = newPref;
    } else {
      this.specific_preferences = rawData;
    }
  }

  resetSpecificPreferences(data: Record<string, unknown> | null = null) {
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

  isResourceType(resourceTypeName: string) {
    return !!this.resource_type && (this.resource_type as ResourceType).name === resourceTypeName;
  }

  _ensureSpecificPreferences() {
    if (!this.specific_preferences) {
      this._coerceSpecificPreferences();
    }
  }

  _getSlurmField(fieldName: string, defaultValue?: unknown) {
    if (this.isResourceType("SLURM") && this.specific_preferences) {
      return (this.specific_preferences as Record<string, unknown>)[fieldName];
    }
    return defaultValue;
  }

  _setSlurmField(fieldName: string, value: unknown) {
    if (!this.isResourceType("SLURM")) {
      return;
    }
    this._ensureSpecificPreferences();
    if (this.specific_preferences) {
      (this.specific_preferences as Record<string, unknown>)[fieldName] = value;
    }
  }

  get allocation_project_number() {
    return this._getSlurmField("allocation_project_number");
  }

  set allocation_project_number(value: unknown) {
    this._setSlurmField("allocation_project_number", value);
  }

  get preferred_batch_queue() {
    return this._getSlurmField("preferred_batch_queue");
  }

  set preferred_batch_queue(value: unknown) {
    this._setSlurmField("preferred_batch_queue", value);
  }

  get quality_of_service() {
    return this._getSlurmField("quality_of_service");
  }

  set quality_of_service(value: unknown) {
    this._setSlurmField("quality_of_service", value);
  }

  get usage_reporting_gateway_id() {
    return this._getSlurmField("usage_reporting_gateway_id");
  }

  set usage_reporting_gateway_id(value: unknown) {
    this._setSlurmField("usage_reporting_gateway_id", value);
  }

  get reservations() {
    return this._getSlurmField("reservations", []);
  }

  set reservations(value: unknown) {
    this._setSlurmField("reservations", value);
  }

  validate() {
    const validationResults: Record<string, unknown> = {};
    if (this.isEmpty(this.login_user_name)) {
      validationResults["login_user_name"] = "Please provide a login username.";
    }
    if (this.isEmpty(this.scratch_location)) {
      validationResults["scratch_location"] = "Please provide a scratch location.";
    }
    if (!this.resource_type) {
      validationResults["resource_type"] = "Please select a resource type.";
    }
    if (this.resource_type && this.specific_preferences) {
      const specificValidation = (this.specific_preferences as { validate: () => Record<string, unknown> }).validate();
      if (specificValidation && Object.keys(specificValidation).length > 0) {
        Object.assign(validationResults, specificValidation);
      }
    }
    return validationResults;
  }
}
