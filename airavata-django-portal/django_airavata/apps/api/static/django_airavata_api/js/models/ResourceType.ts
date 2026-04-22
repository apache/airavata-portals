import BaseEnum from "./BaseEnum";

export default class ResourceType extends BaseEnum {
  static SLURM: ResourceType;
  static AWS: ResourceType;
  static values: ResourceType[];
}
ResourceType.init(["SLURM", "AWS"]);
