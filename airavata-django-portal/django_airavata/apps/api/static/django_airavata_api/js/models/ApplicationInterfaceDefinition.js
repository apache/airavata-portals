import BaseModel from "./BaseModel";
import InputDataObjectType from "./InputDataObjectType";
import OutputDataObjectType from "./OutputDataObjectType";
import DataType from "./DataType";
import Experiment from "./Experiment";

const FIELDS = [
  "application_interface_id",
  "application_name",
  "application_description",
  {
    name: "application_modules",
    type: "string",
    list: true,
  },
  // When saving/updating, the order of the inputs in the application_inputs
  // array determines the 'input_order' that will be applied to each input on
  // the backend. Updating 'input_order' will have no effect.
  {
    name: "application_inputs",
    type: InputDataObjectType,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "application_outputs",
    type: OutputDataObjectType,
    list: true,
    default: BaseModel.defaultNewInstance(Array),
  },
  {
    name: "archive_working_directory",
    type: "boolean",
    default: false,
  },
  {
    name: "has_optional_file_inputs",
    type: "boolean",
    default: false,
  },
  // WithAccess-merged scalar (not on the proto).
  "user_has_write_access",
  // Portal-only queue-settings overrides: not on the proto and not merged into
  // the read response; the backend persists them from the write request body
  // (snake_case keys) into the ApplicationSettings model.
  {
    name: "show_queue_settings",
    type: "boolean",
    default: true,
  },
  {
    name: "queue_settings_calculator_id",
    type: "string",
    default: null,
  },
];

export default class ApplicationInterfaceDefinition extends BaseModel {
  constructor(data = {}) {
    super(FIELDS, data);
  }

  addStandardOutAndStandardErrorOutputs() {
    const stdout = new OutputDataObjectType({
      name: "Standard-Out",
      type: DataType.STDOUT,
      isRequired: true,
      metaData: {
        "file-metadata": {
          "mime-type": "text/plain",
        },
      },
    });
    const stderr = new OutputDataObjectType({
      name: "Standard-Error",
      type: DataType.STDERR,
      isRequired: true,
      metaData: {
        "file-metadata": {
          "mime-type": "text/plain",
        },
      },
    });
    if (!this.application_outputs) {
      this.application_outputs = [];
    }
    this.application_outputs.push(stdout, stderr);
  }

  createExperiment() {
    const experiment = new Experiment();
    experiment.populateInputsOutputsFromApplicationInterface(this);
    experiment.execution_id = this.application_interface_id;
    return experiment;
  }

  get applicationModuleId() {
    if (!this.application_modules || this.application_modules.length > 1) {
      throw new Error(
        `No unique application module exists for interface
        ${this.application_name}: modules=${this.application_modules}`
      );
    }
    return this.application_modules[0];
  }
}
