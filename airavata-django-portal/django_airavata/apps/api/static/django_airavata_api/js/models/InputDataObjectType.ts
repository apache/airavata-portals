import BaseModel from "./BaseModel";
import DataType from "./DataType";
import BooleanExpressionEvaluator from "./dependencies/BooleanExpressionEvaluator";
import { v4 as uuidv4 } from "uuid";
import ValidatorFactory from "./validators/ValidatorFactory";

const FIELDS = [
  "name",
  "value",
  {
    name: "type",
    type: DataType,
    default: DataType.STRING,
  },
  "application_argument",
  {
    name: "standard_input",
    type: "boolean",
    default: false,
  },
  "user_friendly_description",
  "meta_data",
  "input_order",
  {
    name: "is_required",
    type: "boolean",
    default: false,
  },
  {
    name: "required_to_added_to_command_line",
    type: "boolean",
    default: false,
  },
  {
    name: "data_staged",
    type: "boolean",
    default: false,
  },
  "storage_resource_id",
  {
    name: "is_read_only",
    type: "boolean",
    default: false,
  },
  "override_filename",
];

const IS_REQUIRED_DEFAULT = "This field is required.";
const IS_REQUIRED_URI_COLLECTION = "At least one file must be selected.";

export default class InputDataObjectType extends BaseModel {
  [key: string]: unknown;
  static VALID_DATA_TYPES: DataType[];
  private _key: string;

  constructor(data: Record<string, unknown> = {}) {
    super(FIELDS, data);
    this._key = data.key ? (data.key as string) : uuidv4();
    this.show = true;
  }

  get key() {
    return this._key;
  }

  /**
   * Get the UI component id for the editor component to use for this input.
   * Returns null if there is no editor UI component id.
   */
  get editorUIComponentId() {
    const metadata = this._getMetaData();
    if (metadata && "editor" in metadata && "ui-component-id" in (metadata["editor"] as Record<string, unknown>)) {
      return (metadata["editor"] as Record<string, unknown>)["ui-component-id"];
    } else {
      return null;
    }
  }

  /**
   * Get the configuration for the editor component.
   */
  get editorConfig() {
    const metadata = this._getMetaData();
    if (metadata && "editor" in metadata && "config" in (metadata["editor"] as Record<string, unknown>)) {
      return (metadata["editor"] as Record<string, unknown>)["config"];
    } else {
      return {};
    }
  }

  /**
   * Get the validations for the editor component.
   */
  get editorValidations(): Array<{ type: string; value: unknown; message?: string }> {
    const metadata = this._getMetaData();
    if (metadata && "editor" in metadata && "validations" in (metadata["editor"] as Record<string, unknown>)) {
      return (metadata["editor"] as Record<string, unknown>)["validations"] as Array<{ type: string; value: unknown; message?: string }>;
    } else {
      return [];
    }
  }

  /**
   * Get the dependencies for the editor component.
   */
  get editorDependencies(): Record<string, unknown> {
    const metadata = this._getMetaData();
    if (metadata && "editor" in metadata && "dependencies" in (metadata["editor"] as Record<string, unknown>)) {
      return (metadata["editor"] as Record<string, unknown>)["dependencies"] as Record<string, unknown>;
    } else {
      return {};
    }
  }

  _getMetaData() {
    // meta_data could really be anything, here we expect it to be an object
    // so safely check if it is first
    if (this.meta_data && typeof this.meta_data === "object") {
      return this.meta_data as Record<string, unknown>;
    } else {
      return null;
    }
  }

  validate(value?: unknown) {
    const inputValue = typeof value !== "undefined" ? value : this.value;
    const results: Record<string, unknown> = {};
    // Skip running validations when the input isn't shown
    if (!this.show) {
      return results;
    }
    let valueErrorMessages: (string | Promise<string>)[] = [];
    if (this.is_required && this.isEmpty(inputValue)) {
      if (this.type === DataType.URI_COLLECTION) {
        valueErrorMessages.push(IS_REQUIRED_URI_COLLECTION);
      } else {
        valueErrorMessages.push(IS_REQUIRED_DEFAULT);
      }
    }
    // Run through any validations if configured
    if (this.editorValidations.length > 0) {
      const validatorFactory = new ValidatorFactory();
      valueErrorMessages = valueErrorMessages.concat(
        validatorFactory.validate(this.editorValidations, inputValue),
      );
    }
    if (valueErrorMessages.length > 0) {
      results["value"] = valueErrorMessages;
    }
    return results;
  }

  /**
   * Evaluate dependencies on the values of other application inputs.
   */
  evaluateDependencies(inputValues: Record<string, unknown>) {
    if (Object.keys(this.editorDependencies).length > 0) {
      const booleanExpressionEvaluator = new BooleanExpressionEvaluator(inputValues);
      if ("show" in this.editorDependencies) {
        this.show = booleanExpressionEvaluator.evaluate(this.editorDependencies.show as Record<string, unknown>);
        if ("showOptions" in this.editorDependencies) {
          const showOptions = this.editorDependencies.showOptions as Record<string, unknown>;
          if (
            "is_required" in showOptions &&
            showOptions.is_required
          ) {
            this.is_required = this.show;
          }
        }
      }
    }
  }
}

InputDataObjectType.VALID_DATA_TYPES = [
  DataType.STRING,
  DataType.INTEGER,
  DataType.FLOAT,
  DataType.URI,
  DataType.URI_COLLECTION,
];
