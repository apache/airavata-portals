interface ValidatorConfig {
  value: string;
  message?: string;
}

export default class RegularExpressionValidator {
  regex: RegExp;
  customErrorMessage?: string;

  constructor(config: ValidatorConfig) {
    this.regex = new RegExp(config["value"]);
    if ("message" in config) {
      this.customErrorMessage = config["message"];
    }
  }

  validate(value: unknown): string | null {
    if (value === null || typeof value === "undefined") {
      return null;
    }
    let strValue = typeof value !== "string" ? String(value) : value;
    if (!strValue.match(this.regex)) {
      return this.getErrorMessage();
    }
    return null;
  }

  getErrorMessage(): string {
    if (this.customErrorMessage) {
      return this.customErrorMessage;
    } else {
      return "The value must match the regular expression " + this.regex;
    }
  }
}
