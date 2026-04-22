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
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  toJSON() {
    const json = { ...this } as Record<string, unknown>;
    if (json.group_ssh_account_provisioner_configs) {
      json.group_ssh_account_provisioner_configs = (json.group_ssh_account_provisioner_configs as GroupAccountSSHProvisionerConfig[]).map(
        (cfg) => (typeof (cfg as { toJSON?: () => unknown }).toJSON === "function" ? (cfg as { toJSON: () => unknown }).toJSON() : cfg),
      );
    }
    if (json.reservations) {
      json.reservations = (json.reservations as ComputeResourceReservation[]).map((res) =>
        typeof (res as { toJSON?: () => unknown }).toJSON === "function" ? (res as { toJSON: () => unknown }).toJSON() : res,
      );
    }
    return json;
  }

  validate() {
    return {};
  }
}
