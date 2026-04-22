import BaseEnum from "./BaseEnum";

export default class ExperimentState extends BaseEnum {
  static CREATED: ExperimentState;
  static VALIDATED: ExperimentState;
  static SCHEDULED: ExperimentState;
  static LAUNCHED: ExperimentState;
  static EXECUTING: ExperimentState;
  static CANCELING: ExperimentState;
  static CANCELED: ExperimentState;
  static COMPLETED: ExperimentState;
  static FAILED: ExperimentState;
  static values: ExperimentState[];

  get isProgressing() {
    const progressingStates = [
      ExperimentState.SCHEDULED,
      ExperimentState.LAUNCHED,
      ExperimentState.EXECUTING,
      ExperimentState.CANCELING,
    ];
    return progressingStates.indexOf(this) >= 0;
  }
  get isFinished() {
    const finishedStates = [
      ExperimentState.CANCELED,
      ExperimentState.COMPLETED,
      ExperimentState.FAILED,
    ];
    return finishedStates.indexOf(this) >= 0;
  }
}
ExperimentState.init([
  "CREATED",
  "VALIDATED",
  "SCHEDULED",
  "LAUNCHED",
  "EXECUTING",
  "CANCELING",
  "CANCELED",
  "COMPLETED",
  "FAILED",
]);
