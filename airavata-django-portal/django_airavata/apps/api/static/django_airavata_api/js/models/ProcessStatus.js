import BaseModel from "./BaseModel";
import ProcessState from "./ProcessState";

const FIELDS = [
  {
    name: "state",
    type: ProcessState,
  },
  {
    name: "time_of_state_change",
    type: Date,
  },
  "reason",
  "status_id",
];

export default class ProcessStatus extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  get isFinished() {
    return this.state && this.state.isFinished;
  }
}
