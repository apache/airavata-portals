interface ValidationFeedbackEntry {
  invalidFeedback: string[] | null;
  state: false | null;
}

export default {
  createValidationFeedback(
    data: Record<string, unknown> | null | undefined,
    validationErrors: Record<string, string[]> | null | undefined
  ): Record<string, ValidationFeedbackEntry> {
    const validationFeedback: Record<string, ValidationFeedbackEntry> = {};
    if (!data) {
      return validationFeedback;
    }
    for (const fieldName in data) {
      if (Object.prototype.hasOwnProperty.call(data, fieldName)) {
        const errorMessages = validationErrors
          ? validationErrors[fieldName]
          : null;
        if (errorMessages) {
          validationFeedback[fieldName] = {
            invalidFeedback: errorMessages,
            state: false,
          };
        } else {
          validationFeedback[fieldName] = {
            invalidFeedback: null,
            state: null,
          };
        }
      }
    }
    return validationFeedback;
  },
};
