interface ValidatorConfig {
  value: number;
  message?: string;
}

export default class MinLengthValidator {
  minLength: number;
  customErrorMessage?: string;

  constructor(config: ValidatorConfig) {
    this.minLength = config["value"];
    if ("message" in config) {
      this.customErrorMessage = config["message"];
    }
  }

  validate(value: unknown): string | null {
    if (value === null || typeof value === "undefined") {
      return this.getErrorMessage();
    }
    let strValue = typeof value !== "string" ? String(value) : value;
    if (strValue.length < this.minLength) {
      return this.getErrorMessage();
    }
    return null;
  }

  getErrorMessage(): string {
    if (this.customErrorMessage) {
      return this.customErrorMessage;
    } else {
      return "The value must be at least " + this.minLength + " characters in length.";
    }
  }
}
