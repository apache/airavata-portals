import BaseModel from "./BaseModel";
import ErrorModel from "./ErrorModel";
import ExperimentState from "./ExperimentState";
import ExperimentStatus from "./ExperimentStatus";
import InputDataObjectType from "./InputDataObjectType";
import OutputDataObjectType from "./OutputDataObjectType";
import ProcessModel from "./ProcessModel";
import UserConfigurationData from "./UserConfigurationData";

const FIELDS = [
  "experiment_id",
  "project_id",
  "gateway_id",
  {
    name: "experiment_type",
    type: "number",
    default: 0,
  },
  "user_name",
  "experiment_name",
  {
    name: "creation_time",
    type: "date",
  },
  "description",
  "execution_id",
  {
    name: "enable_email_notification",
    type: "boolean",
    default: false,
  },
  {
    name: "email_addresses",
    type: "string",
    list: true,
  },
  {
    name: "user_configuration_data",
    type: UserConfigurationData,
    default: BaseModel.defaultNewInstance(UserConfigurationData),
  },
  {
    name: "experiment_inputs",
    type: InputDataObjectType,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "experiment_outputs",
    type: OutputDataObjectType,
    list: true,
  },
  {
    name: "experiment_status",
    type: ExperimentStatus,
    list: true,
  },
  {
    name: "errors",
    type: ErrorModel,
    list: true,
  },
  {
    name: "processes",
    type: ProcessModel,
    list: true,
  },
  "workflow",
  {
    name: "user_has_write_access",
    type: "boolean",
    default: true,
  },
];

export default class Experiment extends BaseModel {
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
    this.evaluateInputDependencies();
  }

  validate() {
    const validationResults: Record<string, string> = {};
    if (this.isEmpty(this.experiment_name)) {
      validationResults["experiment_name"] = "Please provide a name for this experiment.";
    }
    if (this.isEmpty(this.project_id)) {
      validationResults["project_id"] = "Please select a project.";
    }
    return validationResults;
  }

  get latestStatus() {
    if (this.experiment_status && (this.experiment_status as ExperimentStatus[]).length > 0) {
      return (this.experiment_status as ExperimentStatus[])[(this.experiment_status as ExperimentStatus[]).length - 1];
    } else {
      return null;
    }
  }

  get isProgressing() {
    return this.latestStatus && (this.latestStatus as ExperimentStatus).isProgressing;
  }

  get isFinished() {
    return this.latestStatus && (this.latestStatus as ExperimentStatus).isFinished;
  }

  get hasLaunched() {
    const hasLaunchedStates = [
      ExperimentState.SCHEDULED,
      ExperimentState.LAUNCHED,
      ExperimentState.EXECUTING,
      ExperimentState.CANCELING,
      ExperimentState.CANCELED,
      ExperimentState.FAILED,
      ExperimentState.COMPLETED,
    ];
    return this.latestStatus && hasLaunchedStates.indexOf((this.latestStatus as ExperimentStatus).state as ExperimentState) >= 0;
  }

  get isEditable() {
    return (
      (!this.latestStatus || (this.latestStatus as ExperimentStatus).state === ExperimentState.CREATED) &&
      this.user_has_write_access
    );
  }

  get isCancelable() {
    switch ((this.latestStatus as ExperimentStatus | null)?.state) {
      case ExperimentState.VALIDATED:
      case ExperimentState.SCHEDULED:
      case ExperimentState.LAUNCHED:
      case ExperimentState.EXECUTING:
        return true;
      default:
        return false;
    }
  }

  get resourceHostId() {
    return this.user_configuration_data &&
      (this.user_configuration_data as UserConfigurationData).computational_resource_scheduling
      ? ((this.user_configuration_data as UserConfigurationData).computational_resource_scheduling as { resource_host_id: unknown }).resource_host_id
      : null;
  }

  populateInputsOutputsFromApplicationInterface(applicationInterface: { application_inputs: InputDataObjectType[]; application_outputs: OutputDataObjectType[] }) {
    // Copy application inputs and outputs to the experiment
    this.experiment_inputs = applicationInterface.application_inputs.map((input) => input.clone());
    this.evaluateInputDependencies();
    this.experiment_outputs = applicationInterface.application_outputs.slice();
  }

  evaluateInputDependencies() {
    const inputValues = this._collectInputValues(this.experiment_inputs as InputDataObjectType[]);
    for (const input of this.experiment_inputs as InputDataObjectType[]) {
      input.evaluateDependencies(inputValues);
    }
  }

  getExperimentInput(inputName: string) {
    return (this.experiment_inputs as InputDataObjectType[]).find((inp) => inp.name === inputName);
  }

  getExperimentOutput(outputName: string) {
    return (this.experiment_outputs as OutputDataObjectType[]).find((out) => out.name === outputName);
  }

  _collectInputValues(_inputs?: InputDataObjectType[]) {
    const result: Record<string, unknown> = {};
    (this.experiment_inputs as InputDataObjectType[]).forEach((inp) => {
      result[inp.name as string] = inp.value;
    });
    return result;
  }
}
