import BaseEnum from "./BaseEnum";

export type FieldType = string | (new (...args: unknown[]) => unknown) | null;

export interface FieldDefinition {
  name: string;
  type?: FieldType;
  list?: boolean;
  default?: unknown;
  required?: boolean;
}

export type FieldSpec = string | FieldDefinition;

export default class BaseModel {
  /**
   * Create and optionally populate fields of a model instance.
   * - fields: an Array of field definitions. Each field definition can either
   *   be just the name of the field as a string, or an object with the
   *   following properties:
   *   - name (required)
   *   - type (required: one of 'string', 'boolean', 'number', 'date', or a class reference)
   *   - list (optional, boolean)
   *   - default (optional, the default value to be used, if not specified then null is used)
   * - data: a data object, typically a deserialized JSON response
   */
  constructor(fields: FieldSpec[], data: Record<string, unknown> = {}) {
    fields.forEach((fieldDefinition) => {
      if (typeof fieldDefinition === "string") {
        (this as Record<string, unknown>)[fieldDefinition] = this.convertSimpleField(data[fieldDefinition], null);
      } else {
        // fieldDefinition must be an object
        const fieldName = fieldDefinition.name;
        const fieldType = fieldDefinition.type;
        const fieldIsList =
          typeof fieldDefinition.list !== "undefined" ? fieldDefinition.list : false;
        const fieldDefault =
          typeof fieldDefinition.default !== "undefined"
            ? this.getDefaultValue(fieldDefinition.default)
            : null;
        const fieldValue = data[fieldName];
        if (fieldIsList) {
          (this as Record<string, unknown>)[fieldName] = fieldValue
            ? (fieldValue as unknown[]).map((item) => this.convertField(fieldType, item as Record<string, unknown>, fieldDefault))
            : fieldDefault;
        } else {
          (this as Record<string, unknown>)[fieldName] = this.convertField(fieldType, fieldValue as Record<string, unknown>, fieldDefault);
        }
      }
    });
  }

  convertField(fieldType: FieldType | undefined, fieldValue: unknown, fieldDefault: unknown): unknown {
    if (fieldValue === null || typeof fieldValue === "undefined") {
      return fieldDefault;
    } else if (fieldType === "string" || fieldType === "boolean" || fieldType === "number") {
      return this.convertSimpleField(fieldValue, fieldDefault);
    } else if (fieldType === "date") {
      return this.convertDateField(fieldValue, fieldDefault);
    } else if (typeof fieldType === "function") {
      // Assume that it is another BaseModel class
      return this.convertModelField(fieldType as new (...args: unknown[]) => unknown, fieldValue, fieldDefault);
    }
  }

  convertSimpleField(fieldValue: unknown, fieldDefault: unknown): unknown {
    return typeof fieldValue !== "undefined" ? fieldValue : fieldDefault;
  }

  convertDateField(fieldValue: unknown, fieldDefault: unknown): unknown {
    if (typeof fieldValue === "undefined") {
      return fieldDefault;
    }
    // Handle Unix timestamp strings (milliseconds since epoch)
    if (typeof fieldValue === "string" && /^\d+$/.test(fieldValue)) {
      return new Date(Number(fieldValue));
    }
    return new Date(fieldValue as string | number);
  }

  convertModelField(modelClass: new (...args: unknown[]) => unknown, fieldValue: unknown, fieldDefault: unknown): unknown {
    if (typeof fieldValue !== "undefined") {
      if ((modelClass as unknown as typeof BaseEnum).prototype instanceof BaseEnum) {
        // When cloning the fieldValue is an enum instance
        if (fieldValue instanceof BaseEnum) {
          return fieldValue;
        }
        const enumClass = modelClass as unknown as typeof BaseEnum & { values: BaseEnum[]; byName: (name: string) => BaseEnum | undefined; byValue: (value: number | string) => BaseEnum | undefined };
        let enumValue: BaseEnum | undefined = undefined;
        if (typeof fieldValue === "string") {
          // convert by name if type is string
          enumValue = enumClass.byName(fieldValue);
        } else {
          // Otherwise it is an integer that we need to convert to enum
          enumValue = enumClass.byValue(fieldValue as number | string);
        }
        if (!enumValue) {
          // enum wasn't found, construct an enum instance from the value
          return new BaseEnum(`Unknown value: ${fieldValue}`, fieldValue as number | string);
        } else {
          return enumValue;
        }
      } else if (fieldValue instanceof (modelClass as unknown as new (...args: unknown[]) => object)) {
        // No conversion necessary, just return the fieldValue
        return fieldValue;
      } else {
        return new (modelClass as new (data: unknown) => unknown)(fieldValue);
      }
    }
    return fieldDefault;
  }

  getDefaultValue(fieldDefault: unknown): unknown {
    if (typeof fieldDefault === "function") {
      return (fieldDefault as () => unknown)();
    } else {
      return fieldDefault;
    }
  }

  static defaultNewInstance<T>(classRef: new () => T): () => T {
    return () => new classRef();
  }

  /**
   * Override to provide validation. If there are validation errors this
   * method should return a dictionary where keys are property names and
   * values are an array of error messages.
   */
  validate(..._args: unknown[]): Record<string, unknown> | null {
    return null;
  }

  isEmpty(value: unknown): boolean {
    return (
      value === null ||
      (typeof value === "string" && value.trim() === "") ||
      (value instanceof Array && value.length === 0)
    );
  }

  /**
   * Return a fully deep cloned instance of this instance.
   */
  clone(): this {
    return new (this.constructor as new (data: unknown) => this)(this);
  }
}
