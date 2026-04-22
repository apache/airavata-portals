interface VuelidateField {
  $dirty: boolean;
  $error: boolean;
}

/**
 * Return true/false/null for bootstrap-vue validation state.
 * Returns true when valid, false when invalid, null when untouched.
 */
export function validateState(
  validation: VuelidateField
): boolean | null {
  const { $dirty, $error } = validation;
  return $dirty ? !$error : null;
}

/**
 * Return false if there is a validation error, null otherwise.
 *
 * This is just like validateState except it doesn't return true when valid
 * which is useful if you only want to show invalid feedback.
 */
export function validateStateErrorOnly(
  validation: VuelidateField
): false | null {
  const { $dirty, $error } = validation;
  return $dirty && $error ? false : null;
}
