<template>
  <extended-user-profile-value-editor v-bind="$props">
    <select
      v-model="value"
      :class="['form-select', validateStateErrorOnly(v$.value) === false ? 'is-invalid' : '']"
      @change="onChange"
    >
      <option :value="null" disabled>-- Please select an option --</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
      <option v-if="extendedUserProfileField.other" :value="otherOptionValue">
        Other (please specify)
      </option>
    </select>
    <div v-if="v$.value.$dirty && v$.value.$error" class="invalid-feedback">
      This field is required.
    </div>
    <template v-if="showOther">
      <input
        v-model="other"
        :class="['form-control mt-2', validateState(v$.other) === false ? 'is-invalid' : '']"
        placeholder="Please specify"
        @input="onInput"
      />
      <div v-if="v$.other.$dirty && v$.other.$error" class="invalid-feedback">
        Please specify a value for 'Other'.
      </div>
    </template>
  </extended-user-profile-value-editor>
</template>

<script>
import { mapGetters, mapMutations } from "vuex";
import { useVuelidate } from "@vuelidate/core";
import { required, requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
import ExtendedUserProfileValueEditor from "./ExtendedUserProfileValueEditor.vue";
const OTHER_OPTION = new Object(); // sentinel value

export default {
  components: { ExtendedUserProfileValueEditor },
  props: ["extendedUserProfileField"],
  setup() {
    return { v$: useVuelidate() };
  },
  data() {
    return {
      otherOptionSelected: false,
    };
  },
  computed: {
    ...mapGetters("extendedUserProfile", ["getSingleChoiceValue", "getSingleChoiceOther"]),
    value: {
      get() {
        if (this.showOther) {
          return this.otherOptionValue;
        } else {
          return this.getSingleChoiceValue(this.extendedUserProfileField.id);
        }
      },
      set(value) {
        if (value !== this.otherOptionValue) {
          this.setSingleChoiceValue({
            value,
            id: this.extendedUserProfileField.id,
          });
          this.v$.value.$touch();
        }
      },
    },
    other: {
      get() {
        return this.getSingleChoiceOther(this.extendedUserProfileField.id);
      },
      set(value) {
        this.setSingleChoiceOther({
          value,
          id: this.extendedUserProfileField.id,
        });
        this.v$.other.$touch();
      },
    },
    showOther() {
      const value = this.getSingleChoiceValue(this.extendedUserProfileField.id);
      return (value === null && this.other) || this.otherOptionSelected;
    },
    options() {
      return this.extendedUserProfileField && this.extendedUserProfileField.choices
        ? this.extendedUserProfileField.choices.map((choice) => {
            return {
              value: choice.id,
              text: choice.display_text,
            };
          })
        : [];
    },
    otherOptionValue() {
      return OTHER_OPTION;
    },
    valid() {
      return !this.v$.$invalid;
    },
    required() {
      return this.extendedUserProfileField.required;
    },
  },
  validations() {
    const validations = {
      value: {},
      other: {},
    };
    if (this.showOther) {
      validations.other = { required };
    } else {
      validations.value = { required: requiredIf(() => this.required) };
    }
    return validations;
  },
  methods: {
    ...mapMutations("extendedUserProfile", ["setSingleChoiceValue", "setSingleChoiceOther"]),
    onChange(event) {
      this.otherOptionSelected = event.target.value === String(this.otherOptionValue);
    },
    onInput() {
      this.otherOptionSelected = true;
    },
    validateState: errors.vuelidateHelpers.validateState,
    validateStateErrorOnly: errors.vuelidateHelpers.validateStateErrorOnly,
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
