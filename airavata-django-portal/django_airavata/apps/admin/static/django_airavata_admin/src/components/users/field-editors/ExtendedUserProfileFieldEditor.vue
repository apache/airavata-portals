<template>
  <b-card
    :title="title"
    :border-variant="v$.$anyDirty && v$.$invalid ? 'danger' : null"
  >
    <b-form-group label="Name" label-cols="3" :disabled="disabled">
      <b-form-input v-model="name" :state="validateState(v$.name)" />
      <b-form-invalid-feedback :state="validateState(v$.name)"
        >This field is required.</b-form-invalid-feedback
      >
    </b-form-group>
    <b-form-group
      label="Checkbox Label"
      label-cols="3"
      :disabled="disabled"
      v-if="extendedUserProfileField.field_type === 'user_agreement'"
    >
      <b-form-input
        v-model="checkbox_label"
        :state="validateState(v$.checkbox_label)"
        placeholder="E.g. I accept the Terms of Service listed above"
      />
      <b-form-invalid-feedback :state="validateState(v$.checkbox_label)"
        >This field is required.</b-form-invalid-feedback
      >
    </b-form-group>
    <b-form-group label-cols="3" :disabled="disabled">
      <template #label>
        Help text
        <small class="text-muted text-small">(Optional)</small>
      </template>
      <b-form-input v-model="help_text" />
    </b-form-group>
    <b-form-group :disabled="disabled">
      <b-form-checkbox v-model="required" switch> Required </b-form-checkbox>
    </b-form-group>
    <b-card title="Options" v-if="extendedUserProfileField.supportsChoices">
      <transition-group name="fade">
        <template
          v-for="(choice, index) in extendedUserProfileField.choices"
          :key="choice.key"
        >
          <b-form-group :disabled="disabled">
            <b-input-group>
              <b-form-input
                :model-value="choice.display_text"
                @update:model-value="
                  handleChoiceDisplayTextChanged(choice, $event)
                "
                :state="choiceDisplayTextState(index)"
              />
              <b-button
                @click="handleChoiceMoveUp(choice)"
                :disabled="index === 0"
                v-b-tooltip.hover.left
                title="Move Up"
              >
                <i class="fa fa-arrow-up" aria-hidden="true"></i>
              </b-button>
              <b-button
                @click="handleChoiceMoveDown(choice)"
                :disabled="
                  index === extendedUserProfileField.choices.length - 1
                "
                v-b-tooltip.hover.left
                title="Move Down"
              >
                <i class="fa fa-arrow-down" aria-hidden="true"></i>
              </b-button>
              <b-button
                @click="handleChoiceDeleted(choice)"
                variant="danger"
                v-b-tooltip.hover.left
                title="Delete Option"
              >
                <i class="fa fa-trash" aria-hidden="true"></i>
              </b-button>
            </b-input-group>
            <b-form-invalid-feedback :state="choiceDisplayTextState(index)"
              >This field is required.</b-form-invalid-feedback
            >
          </b-form-group>
        </template>
        <b-form-group
          :key="'other'"
          v-if="extendedUserProfileField.other"
          :disabled="disabled"
        >
          <b-input-group>
            <b-form-input
              placeholder="User will see: Other (please specify)"
              disabled
            />
            <b-button disabled>
              <i class="fa fa-arrow-up" aria-hidden="true"></i>
            </b-button>
            <b-button disabled>
              <i class="fa fa-arrow-down" aria-hidden="true"></i>
            </b-button>
            <b-button
              @click="other = false"
              variant="danger"
              v-b-tooltip.hover.left
              title="Remove Other option"
            >
              <i class="fa fa-trash" aria-hidden="true"></i>
            </b-button>
          </b-input-group>
        </b-form-group>
      </transition-group>
      <b-form-group :disabled="disabled">
        <b-button
          @click="addChoice({ field: extendedUserProfileField })"
          size="sm"
          >Add Option</b-button
        >
      </b-form-group>
      <b-form-group :disabled="disabled">
        <b-form-checkbox v-model="other" switch>
          Allow user to type in an "Other" option
        </b-form-checkbox>
      </b-form-group>
    </b-card>

    <template v-if="links && links.length > 0">
      <transition-group name="fade">
        <b-card
          :title="`Link: ${link.label}`"
          v-for="(link, index) in links"
          :key="link.key"
        >
          <b-form-group label="Label" label-cols="3" :disabled="disabled">
            <b-form-input
              :model-value="link.label"
              @update:model-value="handleLinkLabelChanged(link, $event)"
              :state="linkLabelState(index)"
            />
            <b-form-invalid-feedback :state="linkLabelState(index)"
              >This field is required.</b-form-invalid-feedback
            >
          </b-form-group>
          <b-form-group label="URL" label-cols="3" :disabled="disabled">
            <b-form-input
              :model-value="link.url"
              @update:model-value="handleLinkURLChanged(link, $event)"
              :state="linkUrlState(index)"
            />
            <b-form-invalid-feedback :state="linkUrlState(index)"
              >This field is required.</b-form-invalid-feedback
            >
          </b-form-group>
          <b-row>
            <b-col>
              <b-form-group :disabled="disabled">
                <b-form-checkbox
                  :model-value="link.display_link"
                  @update:model-value="
                    handleLinkDisplayLinkChanged(link, $event)
                  "
                  switch
                >
                  Show as link?
                </b-form-checkbox>
              </b-form-group>
            </b-col>
            <b-col>
              <b-form-group :disabled="disabled">
                <b-form-checkbox
                  :model-value="link.display_inline"
                  @update:model-value="
                    handleLinkDisplayInlineChanged(link, $event)
                  "
                  switch
                >
                  Show inline?
                </b-form-checkbox>
              </b-form-group>
            </b-col>
          </b-row>
          <b-button
            @click="handleLinkDeleted(link)"
            variant="danger"
            size="sm"
            :disabled="disabled"
          >
            Delete Link
          </b-button>
        </b-card>
      </transition-group>
    </template>
    <b-button
      @click="addLink({ field: extendedUserProfileField })"
      size="sm"
      :disabled="disabled"
      >Add Link</b-button
    >
    <b-button
      @click="handleMoveUp({ field: extendedUserProfileField })"
      :disabled="
        disabled ||
        extendedUserProfileFields.indexOf(extendedUserProfileField) === 0
      "
      size="sm"
      >Move Up</b-button
    >
    <b-button
      @click="handleMoveDown({ field: extendedUserProfileField })"
      :disabled="
        disabled ||
        extendedUserProfileFields.indexOf(extendedUserProfileField) ===
          extendedUserProfileFields.length - 1
      "
      size="sm"
      >Move Down</b-button
    >
    <b-button
      @click="handleDelete"
      variant="danger"
      size="sm"
      :disabled="disabled"
      >Delete</b-button
    >
  </b-card>
</template>

<script>
import { mapActions, mapState } from "pinia";
import { useExtendedUserProfileStore } from "../../../store/modules/extendedUserProfile";
import { useVuelidate } from "@vuelidate/core";
import { helpers, required, requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
export default {
  setup() {
    return { v$: useVuelidate() };
  },
  props: ["extendedUserProfileField", "disabled"],
  computed: {
    ...mapState(useExtendedUserProfileStore, ["extendedUserProfileFields"]),
    name: {
      get() {
        return this.extendedUserProfileField.name;
      },
      set(value) {
        this.setName({ value, field: this.extendedUserProfileField });
        this.v$.name.$touch();
      },
    },
    checkbox_label: {
      get() {
        return this.extendedUserProfileField.checkbox_label;
      },
      set(value) {
        this.setCheckboxLabel({ value, field: this.extendedUserProfileField });
        this.v$.checkbox_label.$touch();
      },
    },
    help_text: {
      get() {
        return this.extendedUserProfileField.help_text;
      },
      set(value) {
        this.setHelpText({ value, field: this.extendedUserProfileField });
      },
    },
    required: {
      get() {
        return this.extendedUserProfileField.required;
      },
      set(value) {
        this.setRequired({ value, field: this.extendedUserProfileField });
      },
    },
    other: {
      get() {
        return this.extendedUserProfileField.other;
      },
      set(value) {
        this.setOther({ value, field: this.extendedUserProfileField });
      },
    },
    title() {
      const fieldTypes = {
        text: "Text",
        single_choice: "Single Choice",
        multi_choice: "Multi Choice",
        user_agreement: "User Agreement",
      };
      return `${fieldTypes[this.extendedUserProfileField.field_type]}: ${
        this.name
      }`;
    },
    choices() {
      return this.extendedUserProfileField.choices;
    },
    links() {
      return this.extendedUserProfileField.links;
    },
    valid() {
      return !this.v$.$invalid;
    },
    checkboxLabelIsRequired() {
      return this.extendedUserProfileField.field_type === "user_agreement";
    },
  },
  validations() {
    // @vuelidate/core 2: array element validation uses helpers.forEach instead
    // of the removed `$each`. Per-element results are read from
    // v$.choices.$each.$response.$errors[index] in the template.
    return {
      name: {
        required,
      },
      checkbox_label: {
        required: requiredIf(this.checkboxLabelIsRequired),
      },
      choices: {
        $each: helpers.forEach({
          display_text: {
            required,
          },
        }),
      },
      links: {
        $each: helpers.forEach({
          label: {
            required,
          },
          url: {
            required,
          },
        }),
      },
    };
  },
  methods: {
    ...mapActions(useExtendedUserProfileStore, [
      "setName",
      "setCheckboxLabel",
      "setHelpText",
      "setRequired",
      "setOther",
      "addChoice",
      "updateChoiceDisplayText",
      "deleteChoice",
      "updateChoiceIndex",
      "addLink",
      "updateLinkLabel",
      "updateLinkURL",
      "updateLinkDisplayLink",
      "updateLinkDisplayInline",
      "deleteLink",
      "updateFieldIndex",
      "deleteField",
    ]),
    handleChoiceDisplayTextChanged(choice, display_text) {
      this.updateChoiceDisplayText({ choice, display_text });
      this.v$.choices.$touch();
    },
    handleChoiceDeleted(choice) {
      this.deleteChoice({ field: this.extendedUserProfileField, choice });
    },
    handleChoiceMoveUp(choice) {
      let index = this.extendedUserProfileField.choices.indexOf(choice);
      index--;
      this.updateChoiceIndex({
        field: this.extendedUserProfileField,
        choice,
        index,
      });
    },
    handleChoiceMoveDown(choice) {
      let index = this.extendedUserProfileField.choices.indexOf(choice);
      index++;
      this.updateChoiceIndex({
        field: this.extendedUserProfileField,
        choice,
        index,
      });
    },
    handleLinkLabelChanged(link, label) {
      this.updateLinkLabel({ link, label });
      this.v$.links.$touch();
    },
    handleLinkURLChanged(link, url) {
      this.updateLinkURL({ link, url });
      this.v$.links.$touch();
    },
    handleLinkDisplayLinkChanged(link, display_link) {
      this.updateLinkDisplayLink({ link, display_link });
    },
    handleLinkDisplayInlineChanged(link, display_inline) {
      this.updateLinkDisplayInline({ link, display_inline });
    },
    handleLinkDeleted(link) {
      this.deleteLink({ field: this.extendedUserProfileField, link });
    },
    handleMoveUp({ field }) {
      let index = this.extendedUserProfileFields.indexOf(field);
      index--;
      this.updateFieldIndex({ field, index });
    },
    handleMoveDown({ field }) {
      let index = this.extendedUserProfileFields.indexOf(field);
      index++;
      this.updateFieldIndex({ field, index });
    },
    handleDelete() {
      this.deleteField({
        field: this.extendedUserProfileField,
      });
    },
    validateState: errors.vuelidateHelpers.validateState,
    // Per-element validation state for helpers.forEach arrays (replaces the
    // removed `$each.$iter` per-item validation objects). Mirrors
    // vuelidateHelpers.validateState: null until the array is dirty, then false
    // when the element's named property has errors, true otherwise.
    elementState(arrayValidation, index, property) {
      if (!arrayValidation.$dirty) {
        return null;
      }
      const elementErrors = arrayValidation.$each.$response.$errors[index];
      const propertyErrors = elementErrors ? elementErrors[property] : [];
      return propertyErrors && propertyErrors.length > 0 ? false : true;
    },
    choiceDisplayTextState(index) {
      return this.elementState(this.v$.choices, index, "display_text");
    },
    linkLabelState(index) {
      return this.elementState(this.v$.links, index, "label");
    },
    linkUrlState(index) {
      return this.elementState(this.v$.links, index, "url");
    },
    touch() {
      this.v$.$touch();
    },
  },
  watch: {
    valid: {
      handler(valid) {
        this.$emit(valid ? "valid" : "invalid");
      },
      immediate: true,
    },
  },
};
</script>

<style></style>
