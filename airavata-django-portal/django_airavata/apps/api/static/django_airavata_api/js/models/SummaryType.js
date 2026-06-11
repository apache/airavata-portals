import BaseEnum from "./BaseEnum";

export default class SummaryType extends BaseEnum {}
// writeName: serializes the proto member name (SSH/PASSWD/CERT are bare proto
// names; the 0-sentinel keeps its SUMMARY_TYPE_ prefix).
SummaryType.init(["SUMMARY_TYPE_UNKNOWN", "SSH", "PASSWD", "CERT"], true);
