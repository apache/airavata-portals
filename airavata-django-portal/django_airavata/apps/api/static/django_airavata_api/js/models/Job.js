import BaseModel from "./BaseModel";
import JobStatus from "./JobStatus";

const FIELDS = [
  "job_id",
  "task_id",
  "process_id",
  "job_description",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "job_statuses",
    type: JobStatus,
    list: true,
  },
  "compute_resource_consumed",
  "job_name",
  "working_dir",
  "std_out",
  "std_err",
  "exit_code",
];

export default class Job extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  // get the first job status
  get latestJobStatus() {
    if (this.job_statuses && this.job_statuses.length > 0) {
      return this.job_statuses[this.job_statuses.length - 1];
    } else {
      return null;
    }
  }

  get jobStatusStateName() {
    return this.latestJobStatus ? this.latestJobStatus.job_state.name : null;
  }

  get jobStatusTimeOfStateChange() {
    return this.latestJobStatus
      ? this.latestJobStatus.time_of_state_change
      : null;
  }

  get jobStatusReason() {
    return this.latestJobStatus ? this.latestJobStatus.reason : null;
  }
}
