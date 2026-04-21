import BaseModel from "./BaseModel";
import Experiment from "./Experiment";
import ExperimentStatus from "./ExperimentStatus";
import ExperimentState from "./ExperimentState";

const FIELDS = [
  "experiment_id",
  "project_id",
  "gateway_id",
  {
    name: "creation_time",
    type: "date",
  },
  "user_name",
  "name",
  "description",
  "execution_id",
  "resource_host_id",
  {
    name: "experiment_status",
    type: ExperimentState,
  },
  {
    name: "status_update_time",
    type: "date",
  },
  {
    name: "user_has_write_access",
    type: "boolean",
    default: false,
  },
];

export default class ExperimentSummary extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  get isEditable() {
    return this.convertToExperiment().isEditable;
  }

  convertToExperiment() {
    // Purpose of this is to be able to access computed properties on
    // Experiment.js
    return new Experiment(
      Object.assign({}, this, {
        // Most properties are named the same as on Experiment, but the
        // following require some conversion
        experiment_name: this.name,
        experiment_status: [
          new ExperimentStatus({
            state: this.experiment_status,
            time_of_state_change: this.status_update_time,
          }),
        ],
      }),
    );
  }
}
