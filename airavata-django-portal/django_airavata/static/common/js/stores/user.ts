/**
 * Pinia user store — consolidates three Vuex modules:
 *   - apps/auth/.../store/modules/userProfile.js          (user state)
 *   - apps/auth/.../store/modules/extendedUserProfile.js  (extended profile — auth view)
 *   - apps/admin/.../store/modules/extendedUserProfile.js (extended profile — admin view)
 *
 * Vuex modules stay in place for M3; this store coexists. Consumer migration
 * happens in M4.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { models, services } from "django-airavata-api";
import type {
  User,
  ExtendedUserProfileField,
  ExtendedUserProfileFieldChoice,
  ExtendedUserProfileFieldLink,
  ExtendedUserProfileValue,
  ExtendedUserProfileValueType,
} from "../types/user";

export const useUserStore = defineStore("user", () => {
  // ---------------------------------------------------------------------------
  // State — mirrors Vuex userProfile state
  // ---------------------------------------------------------------------------
  const user = ref<User | null>(null);

  // ---------------------------------------------------------------------------
  // State — mirrors Vuex extendedUserProfile state (auth variant)
  // ---------------------------------------------------------------------------
  const extendedUserProfileFields = ref<ExtendedUserProfileField[] | null>(null);
  const extendedUserProfileValues = ref<ExtendedUserProfileValue[]>([]);

  // ---------------------------------------------------------------------------
  // State — extra tracking used only by admin variant
  // ---------------------------------------------------------------------------
  const deletedExtendedUserProfileFields = ref<ExtendedUserProfileField[]>([]);

  // ---------------------------------------------------------------------------
  // Getters — userProfile
  // ---------------------------------------------------------------------------

  // ---------------------------------------------------------------------------
  // Getters — extendedUserProfile (auth)
  // ---------------------------------------------------------------------------
  const hasExtendedUserProfileFields = computed<boolean>(
    () => extendedUserProfileFields.value != null && extendedUserProfileFields.value.length > 0,
  );

  function getTextValue(id: number): string | null {
    const value = extendedUserProfileValues.value.find((v) => v.ext_user_profile_field === id);
    return value ? (value.text_value ?? null) : null;
  }

  function getSingleChoiceValue(id: number): string | null {
    const value = extendedUserProfileValues.value.find((v) => v.ext_user_profile_field === id);
    if (value && value.choices && value.choices.length === 1) {
      return value.choices[0];
    }
    return null;
  }

  function getSingleChoiceOther(id: number): string | null {
    const value = extendedUserProfileValues.value.find((v) => v.ext_user_profile_field === id);
    return value ? (value.other_value ?? null) : null;
  }

  function getMultiChoiceValue(id: number): string[] {
    const value = extendedUserProfileValues.value.find((v) => v.ext_user_profile_field === id);
    return value && value.choices ? value.choices : [];
  }

  function getMultiChoiceOther(id: number): string | null {
    const value = extendedUserProfileValues.value.find((v) => v.ext_user_profile_field === id);
    return value ? (value.other_value ?? null) : null;
  }

  function getUserAgreementValue(id: number): boolean {
    const value = extendedUserProfileValues.value.find((v) => v.ext_user_profile_field === id);
    return value ? (value.agreement_value ?? false) : false;
  }

  // ---------------------------------------------------------------------------
  // Actions — userProfile
  // ---------------------------------------------------------------------------
  async function loadCurrentUser(): Promise<void> {
    user.value = (await services.UserService.current()) as User;
  }

  async function updateUser(): Promise<void> {
    if (!user.value) return;
    user.value = (await services.UserService.update({
      lookup: user.value.id,
      data: user.value,
    })) as User;
  }

  async function verifyEmailChange({ code }: { code: string }): Promise<void> {
    if (!user.value) return;
    user.value = (await services.UserService.verifyEmailChange({
      lookup: user.value.id,
      data: { code },
    })) as User;
  }

  async function resendEmailVerification(): Promise<void> {
    if (!user.value) return;
    await services.UserService.resendEmailVerification({ lookup: user.value.id });
  }

  // ---------------------------------------------------------------------------
  // Actions — extendedUserProfile (auth variant)
  // ---------------------------------------------------------------------------
  async function loadExtendedUserProfileFields(): Promise<void> {
    extendedUserProfileFields.value =
      (await services.ExtendedUserProfileFieldService.list()) as ExtendedUserProfileField[];
  }

  async function loadExtendedUserProfileValues({
    username,
  }: { username?: string } = {}): Promise<void> {
    const params = username ? { username } : undefined;
    extendedUserProfileValues.value = (await services.ExtendedUserProfileValueService.list(
      params,
    )) as ExtendedUserProfileValue[];
  }

  /** Save (auth variant) — calls saveAll with the full values list. */
  async function saveExtendedUserProfileValues(): Promise<void> {
    const saved = (await services.ExtendedUserProfileValueService.saveAll({
      data: extendedUserProfileValues.value,
    })) as ExtendedUserProfileValue[];
    extendedUserProfileValues.value = saved;
  }

  // ---------------------------------------------------------------------------
  // Mutations — setters for individual extended profile value types
  // ---------------------------------------------------------------------------
  function setTextValue({ id, value }: { id: number; value: string }): void {
    const profileValue = extendedUserProfileValues.value.find(
      (v) => v.ext_user_profile_field === id,
    );
    if (profileValue) {
      profileValue.text_value = value;
    } else {
      extendedUserProfileValues.value.push({
        value_type: "text" as ExtendedUserProfileValueType,
        ext_user_profile_field: id,
        text_value: value,
      });
    }
  }

  function setSingleChoiceValue({ id, value }: { id: number; value: string }): void {
    const profileValue = extendedUserProfileValues.value.find(
      (v) => v.ext_user_profile_field === id,
    );
    if (profileValue) {
      profileValue.choices = [value];
      profileValue.other_value = "";
    } else {
      extendedUserProfileValues.value.push({
        value_type: "single_choice" as ExtendedUserProfileValueType,
        ext_user_profile_field: id,
        choices: [value],
      });
    }
  }

  function setSingleChoiceOther({ id, value }: { id: number; value: string }): void {
    const profileValue = extendedUserProfileValues.value.find(
      (v) => v.ext_user_profile_field === id,
    );
    if (profileValue) {
      profileValue.choices = [];
      profileValue.other_value = value;
    } else {
      extendedUserProfileValues.value.push({
        value_type: "single_choice" as ExtendedUserProfileValueType,
        ext_user_profile_field: id,
        choices: [],
        other_value: value,
      });
    }
  }

  function setMultiChoiceValue({ id, value }: { id: number; value: string[] }): void {
    const profileValue = extendedUserProfileValues.value.find(
      (v) => v.ext_user_profile_field === id,
    );
    if (profileValue) {
      profileValue.choices = value;
    } else {
      extendedUserProfileValues.value.push({
        value_type: "multi_choice" as ExtendedUserProfileValueType,
        ext_user_profile_field: id,
        choices: value,
      });
    }
  }

  function setMultiChoiceOther({ id, value }: { id: number; value: string }): void {
    const profileValue = extendedUserProfileValues.value.find(
      (v) => v.ext_user_profile_field === id,
    );
    if (profileValue) {
      profileValue.other_value = value;
    } else {
      extendedUserProfileValues.value.push({
        value_type: "multi_choice" as ExtendedUserProfileValueType,
        ext_user_profile_field: id,
        choices: [],
        other_value: value,
      });
    }
  }

  function setUserAgreementValue({ id, value }: { id: number; value: boolean }): void {
    const profileValue = extendedUserProfileValues.value.find(
      (v) => v.ext_user_profile_field === id,
    );
    if (profileValue) {
      profileValue.agreement_value = value;
    } else {
      extendedUserProfileValues.value.push({
        value_type: "user_agreement" as ExtendedUserProfileValueType,
        ext_user_profile_field: id,
        agreement_value: value,
      });
    }
  }

  function updateExtendedUserProfileValue({
    extendedUserProfileValue,
  }: {
    extendedUserProfileValue: ExtendedUserProfileValue;
  }): void {
    const index = extendedUserProfileValues.value.findIndex(
      (v) => v.ext_user_profile_field === extendedUserProfileValue.ext_user_profile_field,
    );
    if (index !== -1) {
      extendedUserProfileValues.value.splice(index, 1, extendedUserProfileValue);
    }
  }

  // ---------------------------------------------------------------------------
  // Actions — admin variant extras
  // ---------------------------------------------------------------------------

  /** Save (admin variant) — iterates fields individually, creating or updating. */
  async function saveExtendedUserProfileFields(): Promise<void> {
    if (!extendedUserProfileFields.value) return;
    let order = 1;
    for (const field of extendedUserProfileFields.value) {
      field.order = order++;
      if (field.supportsChoices && field.choices) {
        for (let i = 0; i < field.choices.length; i++) {
          field.choices[i].order = i;
        }
      }
      if (field.links) {
        for (let i = 0; i < field.links.length; i++) {
          field.links[i].order = i;
        }
      }
      if (field.id) {
        await services.ExtendedUserProfileFieldService.update({ lookup: field.id, data: field });
      } else {
        await services.ExtendedUserProfileFieldService.create({ data: field });
      }
    }
    for (const field of deletedExtendedUserProfileFields.value) {
      if (field.id) {
        await services.ExtendedUserProfileFieldService.delete({ lookup: field.id });
      }
    }
    deletedExtendedUserProfileFields.value = [];
    await loadExtendedUserProfileFields();
  }

  /** Accept either a pre-built field object or a field_type to create a new field. */
  function addExtendedUserProfileField({
    field,
    field_type,
  }: {
    field?: ExtendedUserProfileField;
    field_type?: string;
  }): void {
    if (!extendedUserProfileFields.value) {
      extendedUserProfileFields.value = [];
    }
    if (field) {
      extendedUserProfileFields.value.push(field);
    } else if (field_type) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const newField = new (models as any).ExtendedUserProfileField({
        field_type,
        name: `New Field ${extendedUserProfileFields.value.length + 1}`,
        description: "",
        help_text: "",
        required: true,
        links: [],
        other: false,
        choices: [],
        checkbox_label: "",
      }) as ExtendedUserProfileField;
      extendedUserProfileFields.value.push(newField);
    }
  }

  function deleteExtendedUserProfileField({
    field,
  }: {
    field: ExtendedUserProfileField;
  }): void {
    if (!extendedUserProfileFields.value) return;
    const index = extendedUserProfileFields.value.indexOf(field);
    if (index !== -1) {
      extendedUserProfileFields.value.splice(index, 1);
      if (field.id) {
        deletedExtendedUserProfileFields.value.push(field);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Mutations — admin field-editor fine-grained setters
  // These are the per-field property setters used by ExtendedUserProfileFieldEditor.vue
  // ---------------------------------------------------------------------------

  function setFieldName({ field, value }: { field: ExtendedUserProfileField; value: string }): void {
    field.name = value;
  }

  function setFieldCheckboxLabel({ field, value }: { field: ExtendedUserProfileField; value: string }): void {
    field.checkbox_label = value;
  }

  function setFieldHelpText({ field, value }: { field: ExtendedUserProfileField; value: string }): void {
    field.help_text = value;
  }

  function setFieldRequired({ field, value }: { field: ExtendedUserProfileField; value: boolean }): void {
    field.required = value;
  }

  function setFieldOther({ field, value }: { field: ExtendedUserProfileField; value: boolean }): void {
    field.other = value;
  }

  function addFieldChoice({ field }: { field: ExtendedUserProfileField }): void {
    if (!field.choices) field.choices = [];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    field.choices.push(new (models as any).ExtendedUserProfileFieldChoice({
      display_text: "",
    }) as ExtendedUserProfileFieldChoice);
  }

  function updateFieldChoiceDisplayText({ choice, display_text }: { choice: ExtendedUserProfileFieldChoice; display_text: string }): void {
    choice.display_text = display_text;
  }

  function updateFieldChoiceIndex({ field, choice, index }: { field: ExtendedUserProfileField; choice: ExtendedUserProfileFieldChoice; index: number }): void {
    const currentIndex = field.choices.indexOf(choice);
    field.choices.splice(currentIndex, 1);
    field.choices.splice(index, 0, choice);
  }

  function deleteFieldChoice({ field, choice }: { field: ExtendedUserProfileField; choice: ExtendedUserProfileFieldChoice }): void {
    const index = field.choices.indexOf(choice);
    if (index !== -1) field.choices.splice(index, 1);
  }

  function addFieldLink({ field }: { field: ExtendedUserProfileField }): void {
    if (!field.links) field.links = [];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    field.links.push(new (models as any).ExtendedUserProfileFieldLink({
      label: "",
      url: "",
      display_link: true,
      display_inline: false,
    }) as ExtendedUserProfileFieldLink);
  }

  function updateFieldLinkLabel({ link, label }: { link: ExtendedUserProfileFieldLink; label: string }): void {
    link.label = label;
  }

  function updateFieldLinkURL({ link, url }: { link: ExtendedUserProfileFieldLink; url: string }): void {
    link.url = url;
  }

  function updateFieldLinkDisplayLink({ link, display_link }: { link: ExtendedUserProfileFieldLink; display_link: boolean }): void {
    link.display_link = display_link;
  }

  function updateFieldLinkDisplayInline({ link, display_inline }: { link: ExtendedUserProfileFieldLink; display_inline: boolean }): void {
    link.display_inline = display_inline;
  }

  function deleteFieldLink({ field, link }: { field: ExtendedUserProfileField; link: ExtendedUserProfileFieldLink }): void {
    if (!field.links) return;
    const index = field.links.indexOf(link);
    if (index !== -1) field.links.splice(index, 1);
  }

  function updateFieldIndex({ field, index }: { field: ExtendedUserProfileField; index: number }): void {
    if (!extendedUserProfileFields.value) return;
    const currentIndex = extendedUserProfileFields.value.indexOf(field);
    if (currentIndex !== -1) {
      extendedUserProfileFields.value.splice(currentIndex, 1);
      extendedUserProfileFields.value.splice(index, 0, field);
    }
  }

  function setUserFirstName({ first_name }: { first_name: string }): void {
    if (user.value) user.value.first_name = first_name;
  }

  function setUserLastName({ last_name }: { last_name: string }): void {
    if (user.value) user.value.last_name = last_name;
  }

  function setUserEmail({ email }: { email: string }): void {
    if (user.value) user.value.email = email;
  }

  // ---------------------------------------------------------------------------
  // Expose
  // ---------------------------------------------------------------------------
  return {
    // state
    user,
    extendedUserProfileFields,
    extendedUserProfileValues,
    deletedExtendedUserProfileFields,
    // getters
    hasExtendedUserProfileFields,
    getTextValue,
    getSingleChoiceValue,
    getSingleChoiceOther,
    getMultiChoiceValue,
    getMultiChoiceOther,
    getUserAgreementValue,
    // actions — userProfile
    loadCurrentUser,
    updateUser,
    verifyEmailChange,
    resendEmailVerification,
    // actions — extendedUserProfile (auth)
    loadExtendedUserProfileFields,
    loadExtendedUserProfileValues,
    saveExtendedUserProfileValues,
    // setters — value types
    setTextValue,
    setSingleChoiceValue,
    setSingleChoiceOther,
    setMultiChoiceValue,
    setMultiChoiceOther,
    setUserAgreementValue,
    updateExtendedUserProfileValue,
    // actions — admin
    saveExtendedUserProfileFields,
    addExtendedUserProfileField,
    deleteExtendedUserProfileField,
    // fine-grained field mutations (admin field editor)
    setFieldName,
    setFieldCheckboxLabel,
    setFieldHelpText,
    setFieldRequired,
    setFieldOther,
    addFieldChoice,
    updateFieldChoiceDisplayText,
    updateFieldChoiceIndex,
    deleteFieldChoice,
    addFieldLink,
    updateFieldLinkLabel,
    updateFieldLinkURL,
    updateFieldLinkDisplayLink,
    updateFieldLinkDisplayInline,
    deleteFieldLink,
    updateFieldIndex,
    // user property setters
    setUserFirstName,
    setUserLastName,
    setUserEmail,
  };
});
