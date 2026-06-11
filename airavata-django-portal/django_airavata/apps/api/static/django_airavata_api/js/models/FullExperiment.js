import ApplicationModule from "./ApplicationModule";
import BaseModel from "./BaseModel";
import ComputeResourceDescription from "./ComputeResourceDescription";
import DataProduct from "./DataProduct";
import Experiment from "./Experiment";
import Job from "./Job";
import Project from "./Project";

const FIELDS = [
  "experiment_id",
  {
    name: "experiment",
    type: Experiment,
  },
  {
    name: "project",
    type: Project,
  },
  {
    name: "application_module",
    type: ApplicationModule,
  },
  {
    name: "compute_resource",
    type: ComputeResourceDescription,
  },
  {
    name: "output_data_products",
    type: DataProduct,
    list: true,
  },
  {
    name: "input_data_products",
    type: DataProduct,
    list: true,
  },
  {
    name: "job_details",
    type: Job,
    list: true,
  },
  {
    name: "output_views",
    type: Object,
  },
];

export default class FullExperiment extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  get projectName() {
    return this.project ? this.project.name : null;
  }

  get applicationName() {
    return this.application_module
      ? this.application_module.app_module_name
      : null;
  }

  get computeHostName() {
    return this.compute_resource ? this.compute_resource.host_name : null;
  }

  get resourceHostId() {
    return this.experiment.resourceHostId;
  }

  get experimentStatus() {
    return this.experiment.latestStatus;
  }

  get experimentStatusName() {
    return this.experimentStatus ? this.experimentStatus.state.name : null;
  }
}
