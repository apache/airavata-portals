import BaseEnum from "./BaseEnum";

export default class IOType extends BaseEnum {
  static FILE: IOType;
  static PROPERTY: IOType;
  static values: IOType[];
}
IOType.init(["FILE", "PROPERTY"]);
