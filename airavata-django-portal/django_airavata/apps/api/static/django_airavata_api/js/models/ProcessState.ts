import BaseEnum from "./BaseEnum";

export default class ProcessState extends BaseEnum {
  static CREATED: ProcessState;
  static VALIDATED: ProcessState;
  static STARTED: ProcessState;
  static PRE_PROCESSING: ProcessState;
  static CONFIGURING_WORKSPACE: ProcessState;
  static INPUT_DATA_STAGING: ProcessState;
  static EXECUTING: ProcessState;
  static MONITORING: ProcessState;
  static OUTPUT_DATA_STAGING: ProcessState;
  static POST_PROCESSING: ProcessState;
  static COMPLETED: ProcessState;
  static FAILED: ProcessState;
  static CANCELLING: ProcessState;
  static CANCELED: ProcessState;
  static values: ProcessState[];

  get isFinished() {
    const finishedStates = [ProcessState.CANCELED, ProcessState.COMPLETED, ProcessState.FAILED];
    return finishedStates.indexOf(this) >= 0;
  }
}
ProcessState.init([
  "CREATED",
  "VALIDATED",
  "STARTED",
  "PRE_PROCESSING",
  "CONFIGURING_WORKSPACE",
  "INPUT_DATA_STAGING",
  "EXECUTING",
  "MONITORING",
  "OUTPUT_DATA_STAGING",
  "POST_PROCESSING",
  "COMPLETED",
  "FAILED",
  "CANCELLING",
  "CANCELED",
]);
