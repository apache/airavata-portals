<template>
  <extended-user-profile-value-editor v-bind="$props">
    <div class="form-check">
      <input
        v-model="value"
        :class="[
          'form-check-input',
          validateStateErrorOnly(v$.value) === false ? 'is-invalid' : '',
        ]"
        type="checkbox"
        :value="true"
      />
      <label class="form-check-label">
        {{ extendedUserProfileField.checkbox_label }}
      </label>
    </div>
    <div v-if="v$.value.$dirty && v$.value.$error" class="invalid-feedback d-block">
      This field is required.
    </div>
  </extended-user-profile-value-editor>
</template>

<script>
import { mapGetters, mapMutations } from "vuex";
import { useVuelidate } from "@vuelidate/core";
import { errors } from "django-airavata-common-ui";
import ExtendedUserProfileValueEditor from "./ExtendedUserProfileValueEditor.vue";

export default {
  components: { ExtendedUserProfileValueEditor },
  props: ["extendedUserProfileField"],
  setup() {
    return { v$: useVuelidate() };
  },
  computed: {
    ...mapGetters("extendedUserProfile", ["getUserAgreementValue"]),
    value: {
      get() {
        return this.getUserAgreementValue(this.extendedUserProfileField.id);
      },
      set(value) {
        this.setUserAgreementValue({
          value,
          id: this.extendedUserProfileField.id,
        });
        this.v$.value.$touch();
      },
    },
    valid() {
      return !this.v$.$invalid;
    },
    required() {
      return this.extendedUserProfileField.required;
    },
  },
  validations() {
    return {
      value: {
        mustBeTrue: this.mustBeTrue,
      },
    };
  },
  methods: {
    ...mapMutations("extendedUserProfile", ["setUserAgreementValue"]),
    mustBeTrue(value) {
      if (this.required) {
        return value === true;
      } else {
        return true;
      }
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
