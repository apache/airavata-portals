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
  // array determines the 'inputOrder' that will be applied to each input on the
  // backend. Updating 'inputOrder' will have no effect.
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
  "user_has_write_access",
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
  [key: string]: unknown;
  constructor(data: Record<string, unknown> = {}) {
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
    (this.application_outputs as OutputDataObjectType[]).push(stdout, stderr);
  }

  createExperiment() {
    const experiment = new Experiment();
    experiment.populateInputsOutputsFromApplicationInterface(this as unknown as { application_inputs: InputDataObjectType[]; application_outputs: OutputDataObjectType[] });
    experiment.execution_id = this.application_interface_id;
    return experiment;
  }

  get applicationModuleId() {
    if (!this.application_modules || (this.application_modules as string[]).length > 1) {
      throw new Error(
        `No unique application module exists for interface
        ${this.application_name}: modules=${this.application_modules}`,
      );
    }
    return (this.application_modules as string[])[0];
  }
}
