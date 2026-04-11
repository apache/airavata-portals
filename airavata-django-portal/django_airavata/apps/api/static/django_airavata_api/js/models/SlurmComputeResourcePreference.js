import BaseModel from "./BaseModel";
import ComputeResourceReservation from "./ComputeResourceReservation";
import GroupAccountSSHProvisionerConfig from "./GroupAccountSSHProvisionerConfig";

const FIELDS = [
  "allocation_project_number",
  "preferred_batch_queue",
  "quality_of_service",
  "usage_reporting_gateway_id",
  "ssh_account_provisioner",
  {
    name: "group_ssh_account_provisioner_configs",
    type: GroupAccountSSHProvisionerConfig,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  "ssh_account_provisioner_additional_info",
  {
    name: "reservations",
    type: ComputeResourceReservation,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
];

export default class SlurmComputeResourcePreference extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  toJSON() {
    const json = { ...this };
    if (json.group_ssh_account_provisioner_configs) {
      json.group_ssh_account_provisioner_configs = json.group_ssh_account_provisioner_configs.map((cfg) =>
        typeof cfg.toJSON === "function" ? cfg.toJSON() : cfg
      );
    }
    if (json.reservations) {
      json.reservations = json.reservations.map((res) =>
        typeof res.toJSON === "function" ? res.toJSON() : res
      );
    }
    return json;
  }

  validate() {
    return {};
  }
}
