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
  // wire enum NAME ("SINGLE_APPLICATION"); 0-sentinel "EXPERIMENT_TYPE_UNKNOWN".
  {
    name: "experiment_type",
    type: "string",
    default: "EXPERIMENT_TYPE_UNKNOWN",
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
  // merged onto the proto server-side by the WithAccess envelope.
  {
    name: "user_has_write_access",
    type: "boolean",
    default: true,
  },
];

export default class Experiment extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
    this.evaluateInputDependencies();
  }

  validate() {
    let validationResults = {};
    if (this.isEmpty(this.experiment_name)) {
      validationResults["experiment_name"] =
        "Please provide a name for this experiment.";
    }
    if (this.isEmpty(this.project_id)) {
      validationResults["project_id"] = "Please select a project.";
    }
    return validationResults;
  }

  get latestStatus() {
    if (this.experiment_status && this.experiment_status.length > 0) {
      return this.experiment_status[this.experiment_status.length - 1];
    } else {
      return null;
    }
  }

  get isProgressing() {
    return this.latestStatus && this.latestStatus.isProgressing;
  }

  get isFinished() {
    return this.latestStatus && this.latestStatus.isFinished;
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
    return (
      this.latestStatus &&
      hasLaunchedStates.indexOf(this.latestStatus.state) >= 0
    );
  }

  get isEditable() {
    return (
      (!this.latestStatus ||
        this.latestStatus.state === ExperimentState.CREATED) &&
      this.user_has_write_access
    );
  }

  get isCancelable() {
    switch (this.latestStatus.state) {
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
      this.user_configuration_data.computational_resource_scheduling
      ? this.user_configuration_data.computational_resource_scheduling
          .resource_host_id
      : null;
  }

  populateInputsOutputsFromApplicationInterface(applicationInterface) {
    this.experiment_inputs = applicationInterface.application_inputs.map(
      (input) => input.clone()
    );
    this.evaluateInputDependencies();
    this.experiment_outputs = applicationInterface.application_outputs.slice();
  }

  evaluateInputDependencies() {
    const inputValues = this._collectInputValues(this.experiment_inputs);
    for (const input of this.experiment_inputs) {
      input.evaluateDependencies(inputValues);
    }
  }

  getExperimentInput(inputName) {
    return this.experiment_inputs.find(inp => inp.name === inputName);
  }

  getExperimentOutput(outputName) {
    return this.experiment_outputs.find(out => out.name === outputName);
  }

  _collectInputValues() {
    const result = {};
    this.experiment_inputs.forEach((inp) => {
      result[inp.name] = inp.value;
    });
    return result;
  }
}
