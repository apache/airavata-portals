<template>
  <div class="card"
    :title="title"
    :border-variant="$v.$anyDirty && $v.$invalid ? 'danger' : null"
  >
    <div class="mb-3" label="Name" label-cols="3" :disabled="disabled">
      <input class="form-control" v-model="name" :state="validateState($v.name)" />
      <div class="invalid-feedback" :state="validateState($v.name)"
        >This field is required.</b-form-invalid-feedback
      >
    </div>
    <form-group
      label="Checkbox Label"
      label-cols="3"
      :disabled="disabled"
      v-if="extendedUserProfileField.field_type === 'user_agreement'"
    >
      <input class="form-control"
        v-model="checkbox_label"
        :state="validateState($v.checkbox_label)"
        placeholder="E.g. I accept the Terms of Service listed above"
      />
      <div class="invalid-feedback" :state="validateState($v.checkbox_label)"
        >This field is required.</b-form-invalid-feedback
      >
    </div>
    <div class="mb-3" label-cols="3" :disabled="disabled">
      <template #label>
        Help text
        <small class="text-muted text-small">(Optional)</small>
      </template>
      <input class="form-control" v-model="help_text" />
    </div>
    <div class="mb-3" :disabled="disabled">
      <div class="form-check"><input class="form-check-input" type="checkbox" v-model="required" switch> Required </div>
    </div>
    <div class="card" title="Options" v-if="extendedUserProfileField.supportsChoices">
      <transition-group name="fade">
        <template
          v-for="({ $model: choice, display_text: $v_display_text },
          index) in $v.choices.$each.$iter"
        >
          <div class="mb-3" :key="choice.key" :disabled="disabled">
            <div class="input-group">
              <input class="form-control"
                :value="choice.display_text"
                @input="
                  handleChoiceDisplayTextChanged(
                    choice,
                    $event,
                    $v_display_text
                  )
                "
                :state="validateState($v_display_text)"
              />
              <span class="input-group-text">
                <button class="btn"
                  @click="handleChoiceMoveUp(choice)"
                  :disabled="index === String(0)"
                  v-b-tooltip.hover.left
                  title="Move Up"
                >
                  <i class="fa fa-arrow-up" aria-hidden="true"></i>
                </button>
                <button class="btn"
                  @click="handleChoiceMoveDown(choice)"
                  :disabled="
                    index ===
                    String(extendedUserProfileField.choices.length - 1)
                  "
                  v-b-tooltip.hover.left
                  title="Move Down"
                >
                  <i class="fa fa-arrow-down" aria-hidden="true"></i>
                </button>
                <button class="btn"
                  @click="handleChoiceDeleted(choice)"
                  variant="danger"
                  v-b-tooltip.hover.left
                  title="Delete Option"
                >
                  <i class="fa fa-trash" aria-hidden="true"></i>
                </button>
              </span>
            </div>
            <div class="invalid-feedback" :state="validateState($v_display_text)"
              >This field is required.</b-form-invalid-feedback
            >
          </div>
        </template>
        <form-group
          :key="'other'"
          v-if="extendedUserProfileField.other"
          :disabled="disabled"
        >
          <div class="input-group">
            <input class="form-control"
              placeholder="User will see: Other (please specify)"
              disabled
            />
            <span class="input-group-text">
              <button class="btn" disabled>
                <i class="fa fa-arrow-up" aria-hidden="true"></i>
              </button>
              <button class="btn" disabled>
                <i class="fa fa-arrow-down" aria-hidden="true"></i>
              </button>
              <button class="btn"
                @click="other = false"
                variant="danger"
                v-b-tooltip.hover.left
                title="Remove Other option"
              >
                <i class="fa fa-trash" aria-hidden="true"></i>
              </button>
            </span>
          </div>
        </div>
      </transition-group>
      <div class="mb-3" :disabled="disabled">
        <button class="btn"
          @click="addChoice({ field: extendedUserProfileField })"
          size="sm"
          >Add Option</b-button
        >
      </div>
      <div class="mb-3" :disabled="disabled">
        <div class="form-check"><input class="form-check-input" type="checkbox" v-model="other" switch>
          Allow user to type in an "Other" option
        </div>
      </div>
    </div></div>

    <template v-if="links && links.length > 0">
      <transition-group name="fade">
        <div class="card"
          :title="`Link: ${link.label}`"
          v-for="{ $model: link, label: $v_label, url: $v_url } in $v.links
            .$each.$iter"
          :key="link.key"
        >
          <div class="mb-3" label="Label" label-cols="3" :disabled="disabled">
            <input class="form-control"
              :value="link.label"
              @input="handleLinkLabelChanged(link, $event, $v_label)"
              :state="validateState($v_label)"
            />
            <div class="invalid-feedback" :state="validateState($v_label)"
              >This field is required.</b-form-invalid-feedback
            >
          </div>
          <div class="mb-3" label="URL" label-cols="3" :disabled="disabled">
            <input class="form-control"
              :value="link.url"
              @input="handleLinkURLChanged(link, $event, $v_url)"
              :state="validateState($v_url)"
            />
            <div class="invalid-feedback" :state="validateState($v_url)"
              >This field is required.</b-form-invalid-feedback
            >
          </div>
          <div class="row">
            <div>
              <div class="mb-3" :disabled="disabled">
                <form-checkbox
                  :checked="link.display_link"
                  @input="handleLinkDisplayLinkChanged(link, $event)"
                  switch
                >
                  Show as link?
                </div>
              </div>
            </div>
            <div>
              <div class="mb-3" :disabled="disabled">
                <form-checkbox
                  :checked="link.display_inline"
                  @input="handleLinkDisplayInlineChanged(link, $event)"
                  switch
                >
                  Show inline?
                </div>
              </div>
            </div>
          </div>
          <button class="btn"
            @click="handleLinkDeleted(link)"
            variant="danger"
            size="sm"
            :disabled="disabled"
          >
            Delete Link
          </button>
        </div></div>
      </transition-group>
    </template>
    <button class="btn"
      @click="addLink({ field: extendedUserProfileField })"
      size="sm"
      :disabled="disabled"
      >Add Link</b-button
    >
    <button class="btn"
      @click="handleMoveUp({ field: extendedUserProfileField })"
      :disabled="
        disabled ||
        extendedUserProfileFields.indexOf(extendedUserProfileField) === 0
      "
      size="sm"
      >Move Up</b-button
    >
    <button class="btn"
      @click="handleMoveDown({ field: extendedUserProfileField })"
      :disabled="
        disabled ||
        extendedUserProfileFields.indexOf(extendedUserProfileField) ===
          extendedUserProfileFields.length - 1
      "
      size="sm"
      >Move Down</b-button
    >
    <button class="btn"
      @click="handleDelete"
      variant="danger"
      size="sm"
      :disabled="disabled"
      >Delete</b-button
    >
  </div></div>
</template>

<script>
import { mapGetters, mapMutations } from "vuex";
import { validationMixin } from "vuelidate";
import { required, requiredIf } from "vuelidate/lib/validators";
import { errors } from "django-airavata-common-ui";
export default {
  mixins: [validationMixin],
  props: ["extendedUserProfileField", "disabled"],
  computed: {
    ...mapGetters("extendedUserProfile", ["extendedUserProfileFields"]),
    name: {
      get() {
        return this.extendedUserProfileField.name;
      },
      set(value) {
        this.setName({ value, field: this.extendedUserProfileField });
        this.$v.name.$touch();
      },
    },
    checkbox_label: {
      get() {
        return this.extendedUserProfileField.checkbox_label;
      },
      set(value) {
        this.setCheckboxLabel({ value, field: this.extendedUserProfileField });
        this.$v.checkbox_label.$touch();
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
      return !this.$v.$invalid;
    },
    checkboxLabelIsRequired() {
      return this.extendedUserProfileField.field_type === "user_agreement";
    },
  },
  validations() {
    return {
      name: {
        required,
      },
      checkbox_label: {
        required: requiredIf("checkboxLabelIsRequired"),
      },
      choices: {
        $each: {
          display_text: {
            required,
          },
        },
      },
      links: {
        $each: {
          label: {
            required,
          },
          url: {
            required,
          },
        },
      },
    };
  },
  methods: {
    ...mapMutations("extendedUserProfile", [
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
    handleChoiceDisplayTextChanged(choice, display_text, $v) {
      this.updateChoiceDisplayText({ choice, display_text });
      $v.$touch();
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
    handleLinkLabelChanged(link, label, $v) {
      this.updateLinkLabel({ link, label });
      $v.$touch();
    },
    handleLinkURLChanged(link, url, $v) {
      this.updateLinkURL({ link, url });
      $v.$touch();
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
    touch() {
      this.$v.$touch();
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
