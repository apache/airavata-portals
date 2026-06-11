import BaseModel from "./BaseModel";
import ExperimentState from "./ExperimentState";

const FIELDS = [
  {
    name: "state",
    type: ExperimentState,
  },
  {
    name: "time_of_state_change",
    type: "date",
  },
  "reason",
  "status_id",
];

export default class ExperimentStatus extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  get isProgressing() {
    return this.state && this.state.isProgressing;
  }

  get isFinished() {
    return this.state && this.state.isFinished;
  }
}
