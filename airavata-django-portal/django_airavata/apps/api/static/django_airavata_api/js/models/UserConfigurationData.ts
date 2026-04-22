import BaseModel from "./BaseModel";
import ComputationalResourceSchedulingModel from "./ComputationalResourceSchedulingModel";

const FIELDS = [
  {
    name: "airavata_auto_schedule",
    type: "boolean",
    default: false,
  },
  {
    name: "override_manual_scheduled_params",
    type: "boolean",
    default: false,
  },
  {
    name: "share_experiment_publicly",
    type: "boolean",
    default: false,
  },
  {
    name: "computational_resource_scheduling",
    type: ComputationalResourceSchedulingModel,
    default: BaseModel.defaultNewInstance(ComputationalResourceSchedulingModel),
  },
  {
    name: "throttle_resources",
    type: "boolean",
    default: false,
  },
  "user_dn",
  {
    name: "generate_cert",
    type: "boolean",
    default: false,
  },
  "input_storage_resource_id",
  "output_storage_resource_id",
  "experiment_data_dir",
  {
    name: "use_user_cr_pref",
    type: "boolean",
    default: false,
  },
  "group_resource_profile_id",
  "auto_scheduled_comp_resource_scheduling_list",
];

export default class UserConfigurationData extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  validate() {
    const validationResults: Record<string, unknown> = {};
    const computationalResourceSchedulingValidation = (this.computational_resource_scheduling as ComputationalResourceSchedulingModel).validate();
    if (Object.keys(computationalResourceSchedulingValidation).length > 0) {
      validationResults["computational_resource_scheduling"] =
        computationalResourceSchedulingValidation;
    }
    return validationResults;
  }
}
