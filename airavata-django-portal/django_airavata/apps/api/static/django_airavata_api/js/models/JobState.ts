import BaseEnum from "./BaseEnum";

export default class JobState extends BaseEnum {
  static SUBMITTED: JobState;
  static QUEUED: JobState;
  static ACTIVE: JobState;
  static COMPLETE: JobState;
  static CANCELED: JobState;
  static FAILED: JobState;
  static SUSPENDED: JobState;
  static UNKNOWN: JobState;
  static NON_CRITICAL_FAIL: JobState;
  static values: JobState[];
}
JobState.init([
  "SUBMITTED",
  "QUEUED",
  "ACTIVE",
  "COMPLETE",
  "CANCELED",
  "FAILED",
  "SUSPENDED",
  "UNKNOWN",
  "NON_CRITICAL_FAIL",
]);
