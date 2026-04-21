<template>
  <extended-user-profile-value-editor v-bind="$props">
    <input
      v-model="value"
      :class="['form-control', validateState(v$.value) === false ? 'is-invalid' : '']"
    />
    <div v-if="v$.value.$dirty && v$.value.$error" class="invalid-feedback">
      This field is required.
    </div>
  </extended-user-profile-value-editor>
</template>

<script>
import { mapGetters, mapMutations } from "vuex";
import { useVuelidate } from "@vuelidate/core";
import { requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
import ExtendedUserProfileValueEditor from "./ExtendedUserProfileValueEditor.vue";
export default {
  components: { ExtendedUserProfileValueEditor },
  props: ["extendedUserProfileField"],
  setup() {
    return { v$: useVuelidate() };
  },
  computed: {
    ...mapGetters("extendedUserProfile", ["getTextValue"]),
    value: {
      get() {
        return this.getTextValue(this.extendedUserProfileField.id);
      },
      set(value) {
        this.setTextValue({ value, id: this.extendedUserProfileField.id });
        this.v$.$touch();
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
        required: requiredIf(() => this.required),
      },
    };
  },
  methods: {
    ...mapMutations("extendedUserProfile", ["setTextValue"]),
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
