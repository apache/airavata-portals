import BaseModel from "./BaseModel";
import ExperimentSummary from "./ExperimentSummary";

const FIELDS = [
  "all_experiment_count",
  "completed_experiment_count",
  "cancelled_experiment_count",
  "failed_experiment_count",
  "created_experiment_count",
  "running_experiment_count",
  {
    name: "all_experiments",
    type: ExperimentSummary,
    list: true,
  },
  {
    name: "completed_experiments",
    type: ExperimentSummary,
    list: true,
  },
  {
    name: "failed_experiments",
    type: ExperimentSummary,
    list: true,
  },
  {
    name: "cancelled_experiments",
    type: ExperimentSummary,
    list: true,
  },
  {
    name: "created_experiments",
    type: ExperimentSummary,
    list: true,
  },
  { name: "running_experiments", type: ExperimentSummary, list: true },
];

export default class ExperimentStatistics extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }
}
