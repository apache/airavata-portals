import BaseModel from "./BaseModel";
import ProcessStatus from "./ProcessStatus";
import InputDataObjectType from "./InputDataObjectType";
import OutputDataObjectType from "./OutputDataObjectType";
import ComputationalResourceSchedulingModel from "./ComputationalResourceSchedulingModel";
import Task from "./Task";
import ErrorModel from "./ErrorModel";
import ProcessWorkflow from "./ProcessWorkflow";

const FIELDS = [
  "process_id",
  "experiment_id",
  {
    name: "creation_time",
    type: "date",
  },
  {
    name: "last_update_time",
    type: "date",
  },
  {
    name: "process_statuses",
    type: ProcessStatus,
    list: true,
  },
  "process_detail",
  "application_interface_id",
  "application_deployment_id",
  "compute_resource_id",
  {
    name: "process_inputs",
    type: InputDataObjectType,
    list: true,
  },
  {
    name: "process_outputs",
    type: OutputDataObjectType,
    list: true,
  },
  {
    name: "process_resource_schedule",
    type: ComputationalResourceSchedulingModel,
  },
  {
    name: "tasks",
    type: Task,
    list: true,
  },
  "task_dag",
  {
    name: "process_errors",
    type: ErrorModel,
    list: true,
  },
  "gateway_execution_id",
  "enable_email_notification",
  "email_addresses",
  "input_storage_resource_id",
  "output_storage_resource_id",
  "user_dn",
  "generate_cert",
  "experiment_data_dir",
  "user_name",
  "use_user_cr_pref",
  "group_resource_profile_id",
  {
    name: "process_workflows",
    type: ProcessWorkflow,
    list: true,
  },
];

export default class ProcessModel extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  /**
   * Return tasks sorted by task DAG order.
   */
  get sortedTasks() {
    const tasksArrCopy = this.tasks.slice();
    tasksArrCopy.sort((a, b) => {
      const aIndex = this.taskDagArray.findIndex((t) => t === a.task_id);
      const bIndex = this.taskDagArray.findIndex((t) => t === b.task_id);
      return aIndex - bIndex;
    });
    return tasksArrCopy;
  }

  get taskDagArray() {
    return this.task_dag ? this.task_dag.split(",") : [];
  }
}
