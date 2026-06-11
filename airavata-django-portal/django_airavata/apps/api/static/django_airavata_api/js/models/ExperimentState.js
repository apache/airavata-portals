import BaseEnum from "./BaseEnum";

export default class ExperimentState extends BaseEnum {
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
  "EXPERIMENT_STATE_UNKNOWN",
  "EXPERIMENT_STATE_CREATED",
  "EXPERIMENT_STATE_VALIDATED",
  "EXPERIMENT_STATE_SCHEDULED",
  "EXPERIMENT_STATE_LAUNCHED",
  "EXPERIMENT_STATE_EXECUTING",
  "EXPERIMENT_STATE_CANCELING",
  "EXPERIMENT_STATE_CANCELED",
  "EXPERIMENT_STATE_COMPLETED",
  "EXPERIMENT_STATE_FAILED",
]);
