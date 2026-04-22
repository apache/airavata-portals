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
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  get isProgressing() {
    return this.state && (this.state as ExperimentState).isProgressing;
  }

  get isFinished() {
    return this.state && (this.state as ExperimentState).isFinished;
  }
}
