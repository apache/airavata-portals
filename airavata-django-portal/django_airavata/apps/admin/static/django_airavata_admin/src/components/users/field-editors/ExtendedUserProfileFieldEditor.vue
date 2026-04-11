<template>
  <div class="card">
    <div class="card-header">{{ title }}</div>
    <div class="card-body">
      <div class="mb-3">
        <label class="form-label">Name</label>
        <input :class="['form-control', validateState(v$.name) === false ? 'is-invalid' : '']" v-model="name" />
        <div class="invalid-feedback" v-if="v$.name.$dirty && v$.name.$error"
          >This field is required.</div
        >
      </div>
      <form-group
        label="Checkbox Label"
        :disabled="disabled"
        v-if="extendedUserProfileField.field_type === 'user_agreement'"
      >
        <input :class="['form-control', validateState(v$.checkbox_label) === false ? 'is-invalid' : '']"
          v-model="checkbox_label"
          placeholder="E.g. I accept the Terms of Service listed above"
        />
        <div class="invalid-feedback" v-if="v$.checkbox_label.$dirty && v$.checkbox_label.$error"
          >This field is required.</div
        >
      </form-group>
      <div class="mb-3">
        <label class="form-label">Help text <small class="text-muted">(Optional)</small></label>
        <input class="form-control" v-model="help_text" />
      </div>
      <div class="mb-3">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" v-model="required" id="required-check" />
          <label class="form-check-label" for="required-check">Required</label>
        </div>
      </div>
      <div class="card mb-3" v-if="extendedUserProfileField.supportsChoices">
        <div class="card-header">Options</div>
        <div class="card-body">
          <transition-group name="fade">
            <template v-for="(choice, index) in extendedUserProfileField.choices" :key="choice.key">
              <div :class="['mb-3', { 'opacity-50': disabled }]">
                <div class="input-group">
                  <input :class="['form-control', !choice.display_text ? 'is-invalid' : '']"
                    :value="choice.display_text"
                    @input="handleChoiceDisplayTextChanged(choice, $event)"
                  />
                  <span class="input-group-text">
                    <button class="btn btn-sm"
                      @click="handleChoiceMoveUp(choice)"
                      :disabled="index === 0"
                      title="Move Up"
                    >
                      <i class="fa fa-arrow-up" aria-hidden="true"></i>
                    </button>
                    <button class="btn btn-sm"
                      @click="handleChoiceMoveDown(choice)"
                      :disabled="index === extendedUserProfileField.choices.length - 1"
                      title="Move Down"
                    >
                      <i class="fa fa-arrow-down" aria-hidden="true"></i>
                    </button>
                    <button class="btn btn-sm btn-danger"
                      @click="handleChoiceDeleted(choice)"
                      title="Delete Option"
                    >
                      <i class="fa fa-trash" aria-hidden="true"></i>
                    </button>
                  </span>
                </div>
                <div class="invalid-feedback d-block" v-if="!choice.display_text"
                  >This field is required.</div
                >
              </div>
            </template>
            <div v-if="extendedUserProfileField.other" :key="'other'" class="mb-3">
              <div class="input-group">
                <input class="form-control"
                  placeholder="User will see: Other (please specify)"
                  disabled
                />
                <span class="input-group-text">
                  <button class="btn btn-sm" disabled>
                    <i class="fa fa-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button class="btn btn-sm" disabled>
                    <i class="fa fa-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button class="btn btn-sm btn-danger"
                    @click="other = false"
                    title="Remove Other option"
                  >
                    <i class="fa fa-trash" aria-hidden="true"></i>
                  </button>
                </span>
              </div>
            </div>
          </transition-group>
          <div class="mb-3">
            <button class="btn btn-sm btn-secondary"
              @click="addChoice({ field: extendedUserProfileField })"
              >Add Option</button
            >
          </div>
          <div class="mb-3">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" v-model="other" id="other-check" />
              <label class="form-check-label" for="other-check">
                Allow user to type in an "Other" option
              </label>
            </div>
          </div>
        </div>
      </div>

      <template v-if="links && links.length > 0">
        <transition-group name="fade">
          <div class="card mb-2"
            v-for="(link, linkIdx) in links"
            :key="link.key"
          >
            <div class="card-header">Link: {{ link.label }}</div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">Label</label>
                <input :class="['form-control', !link.label ? 'is-invalid' : '']"
                  :value="link.label"
                  @input="handleLinkLabelChanged(link, $event)"
                />
                <div class="invalid-feedback" v-if="!link.label"
                  >This field is required.</div
                >
              </div>
              <div class="mb-3">
                <label class="form-label">URL</label>
                <input :class="['form-control', !link.url ? 'is-invalid' : '']"
                  :value="link.url"
                  @input="handleLinkURLChanged(link, $event)"
                />
                <div class="invalid-feedback" v-if="!link.url"
                  >This field is required.</div
                >
              </div>
              <div class="row mb-2">
                <div class="col">
                  <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox"
                      :checked="link.display_link"
                      @change="handleLinkDisplayLinkChanged(link, $event.target.checked)"
                      :id="`display-link-${linkIdx}`"
                    />
                    <label class="form-check-label" :for="`display-link-${linkIdx}`">Show as link?</label>
                  </div>
                </div>
                <div class="col">
                  <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox"
                      :checked="link.display_inline"
                      @change="handleLinkDisplayInlineChanged(link, $event.target.checked)"
                      :id="`display-inline-${linkIdx}`"
                    />
                    <label class="form-check-label" :for="`display-inline-${linkIdx}`">Show inline?</label>
                  </div>
                </div>
              </div>
              <button class="btn btn-sm btn-danger"
                @click="handleLinkDeleted(link)"
                :disabled="disabled"
              >
                Delete Link
              </button>
            </div>
          </div>
        </transition-group>
      </template>
      <div class="d-flex gap-2 mt-2">
        <button class="btn btn-sm btn-secondary"
          @click="addLink({ field: extendedUserProfileField })"
          :disabled="disabled"
          >Add Link</button
        >
        <button class="btn btn-sm btn-secondary"
          @click="handleMoveUp({ field: extendedUserProfileField })"
          :disabled="disabled || extendedUserProfileFields.indexOf(extendedUserProfileField) === 0"
          >Move Up</button
        >
        <button class="btn btn-sm btn-secondary"
          @click="handleMoveDown({ field: extendedUserProfileField })"
          :disabled="disabled || extendedUserProfileFields.indexOf(extendedUserProfileField) === extendedUserProfileFields.length - 1"
          >Move Down</button
        >
        <button class="btn btn-sm btn-danger"
          @click="handleDelete"
          :disabled="disabled"
          >Delete</button
        >
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapMutations } from "vuex";
import { useVuelidate } from "@vuelidate/core";
import { required, requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
export default {
  props: ["extendedUserProfileField", "disabled"],
  setup() {
    return { v$: useVuelidate() };
  },
  computed: {
    ...mapGetters("extendedUserProfile", ["extendedUserProfileFields"]),
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
      return `${fieldTypes[this.extendedUserProfileField.field_type]}: ${this.name}`;
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
    return {
      name: { required },
      checkbox_label: {
        required: requiredIf(() => this.checkboxLabelIsRequired),
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
    handleChoiceDisplayTextChanged(choice, event) {
      this.updateChoiceDisplayText({ choice, display_text: event.target.value });
    },
    handleChoiceDeleted(choice) {
      this.deleteChoice({ field: this.extendedUserProfileField, choice });
    },
    handleChoiceMoveUp(choice) {
      let index = this.extendedUserProfileField.choices.indexOf(choice);
      index--;
      this.updateChoiceIndex({ field: this.extendedUserProfileField, choice, index });
    },
    handleChoiceMoveDown(choice) {
      let index = this.extendedUserProfileField.choices.indexOf(choice);
      index++;
      this.updateChoiceIndex({ field: this.extendedUserProfileField, choice, index });
    },
    handleLinkLabelChanged(link, event) {
      this.updateLinkLabel({ link, label: event.target.value });
    },
    handleLinkURLChanged(link, event) {
      this.updateLinkURL({ link, url: event.target.value });
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
      this.deleteField({ field: this.extendedUserProfileField });
    },
    validateState: errors.vuelidateHelpers.validateState,
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
