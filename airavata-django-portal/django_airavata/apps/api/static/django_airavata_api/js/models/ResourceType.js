import BaseEnum from "./BaseEnum";

// group-resource-profile ResourceType (SLURM/AWS compute backends); NOT the
// sharing-service ResourceType (PROJECT/EXPERIMENT/...).
export default class ResourceType extends BaseEnum {}
ResourceType.init(["RESOURCE_TYPE_UNKNOWN", "SLURM", "AWS"]);

