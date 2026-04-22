import MaxLengthValidator from "./MaxLengthValidator";
import MinLengthValidator from "./MinLengthValidator";
import RegularExpressionValidator from "./RegularExpressionValidator";

interface ValidationConfig {
  type: string;
  value: unknown;
  message?: string;
}

type ValidatorClass = typeof MaxLengthValidator | typeof MinLengthValidator | typeof RegularExpressionValidator;

const VALIDATOR_MAPPING: Record<string, ValidatorClass> = {
  "max-length": MaxLengthValidator,
  "min-length": MinLengthValidator,
  regex: RegularExpressionValidator,
};

export default class ValidatorFactory {
  validate(validationsConfig: ValidationConfig[], value: unknown): Promise<string>[] {
    const errorMessages: Promise<string>[] = [];
    validationsConfig.forEach((validation) => {
      const validatorClass = VALIDATOR_MAPPING[validation.type];
      const validator = new (validatorClass as new (config: ValidationConfig) => { validate: (v: unknown) => string | null })(validation);
      const errorMessage = validator.validate(value);
      if (errorMessage !== null) {
        errorMessages.push(Promise.resolve(errorMessage));
      }
    });
    return errorMessages;
  }
}
