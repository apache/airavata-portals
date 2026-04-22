/**
 * Type definitions for user-related Pinia store (user.ts).
 * Derived from the Vuex userProfile + extendedUserProfile modules in:
 *   - apps/auth/static/.../store/modules/userProfile.js
 *   - apps/auth/static/.../store/modules/extendedUserProfile.js
 *   - apps/admin/static/.../store/modules/extendedUserProfile.js
 */

export interface PendingEmailChange {
  email_address: string;
}

export interface User {
  id: string;
  username: string;
  username_valid: boolean;
  email: string;
  first_name: string;
  last_name: string;
  complete: boolean;
  ext_user_profile_valid: boolean;
  pending_email_change?: PendingEmailChange | null;
}

export interface ExtendedUserProfileFieldChoice {
  id?: number;
  display_text: string;
  order?: number;
}

export interface ExtendedUserProfileFieldLink {
  id?: number;
  label: string;
  url: string;
  display_link: boolean;
  display_inline: boolean;
  order?: number;
}

export interface ExtendedUserProfileField {
  id?: number;
  name: string;
  help_text: string | null;
  required: boolean;
  field_type: string;
  order?: number;
  other?: boolean;
  checkbox_label?: string;
  description?: string;
  choices: ExtendedUserProfileFieldChoice[];
  links: ExtendedUserProfileFieldLink[];
  /** Computed property on the model (from admin store usage) */
  supportsChoices?: boolean;
}

export type ExtendedUserProfileValueType =
  | "text"
  | "single_choice"
  | "multi_choice"
  | "user_agreement";

export interface ExtendedUserProfileValue {
  ext_user_profile_field: number;
  value_type?: ExtendedUserProfileValueType;
  /** For text fields */
  text_value?: string;
  /** For single/multi-choice fields */
  choices?: string[];
  /** For single/multi-choice fields with "other" option */
  other_value?: string;
  /** For user-agreement fields */
  agreement_value?: boolean;
}
