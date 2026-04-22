import BaseEnum from "./BaseEnum";

export default class SummaryType extends BaseEnum {
  static SSH: SummaryType;
  static PASSWD: SummaryType;
  static CERT: SummaryType;
  static values: SummaryType[];
}
SummaryType.init(["SSH", "PASSWD", "CERT"], true);
