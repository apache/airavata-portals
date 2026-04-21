import BaseEnum from "./BaseEnum";

export default class ResourceType extends BaseEnum {}
ResourceType.init(["SLURM", "AWS"]);
