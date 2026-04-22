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
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
  }

  get projectName() {
    return this.project ? (this.project as Project).name : null;
  }

  get applicationName() {
    return this.application_module ? (this.application_module as ApplicationModule).app_module_name : null;
  }

  get computeHostName() {
    return this.compute_resource ? (this.compute_resource as ComputeResourceDescription).host_name : null;
  }

  get resourceHostId() {
    return (this.experiment as Experiment).user_configuration_data &&
      ((this.experiment as Experiment).user_configuration_data as { computational_resource_scheduling: unknown }).computational_resource_scheduling
      ? (((this.experiment as Experiment).user_configuration_data as Record<string, unknown>).computational_resource_scheduling as { resource_host_id: unknown }).resource_host_id
      : null;
  }

  get experimentStatus() {
    return (this.experiment as Experiment).latestStatus;
  }

  get experimentStatusName() {
    return this.experimentStatus ? ((this.experimentStatus as { state: { name: string } }).state.name) : null;
  }
}
