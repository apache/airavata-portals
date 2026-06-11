import BaseEnum from "./BaseEnum";

export default class JobState extends BaseEnum {}
JobState.init([
  "JOB_STATE_UNKNOWN",
  "SUBMITTED",
  "QUEUED",
  "ACTIVE",
  "COMPLETE",
  "CANCELED",
  "FAILED",
  "SUSPENDED",
  "NON_CRITICAL_FAIL",
]);
