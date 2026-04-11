<template>
  <extended-user-profile-value-editor v-bind="$props">
    <div>
      <div v-for="option in options" :key="option.value" class="form-check">
        <input :class="['form-check-input', validateStateErrorOnly(v$.value) === false ? 'is-invalid' : '']" type="checkbox"
          :value="option.value"
          v-model="value"
          @change="onChange"
        />
        <label class="form-check-label">{{ option.text }}</label>
      </div>
      <div v-if="extendedUserProfileField.other" class="form-check">
        <input class="form-check-input" type="checkbox"
          :value="otherOptionValue"
          v-model="value"
          @change="onChange"
        />
        <label class="form-check-label">Other (please specify)</label>
      </div>
      <div class="invalid-feedback d-block" v-if="v$.value.$dirty && v$.value.$error"
        >This field is required.</div
      >
    </div>
    <template v-if="showOther">
      <input :class="['form-control mt-2', validateState(v$.other) === false ? 'is-invalid' : '']"
        v-model="other"
        placeholder="Please specify"
        @input="onInput"
      />
      <div class="invalid-feedback" v-if="v$.other.$dirty && v$.other.$error"
        >Please specify a value for 'Other'.</div
      >
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
    ...mapGetters("extendedUserProfile", [
      "getMultiChoiceValue",
      "getMultiChoiceOther",
    ]),
    value: {
      get() {
        const copy = this.getMultiChoiceValue(
          this.extendedUserProfileField.id
        ).slice();
        if (this.showOther) {
          copy.push(this.otherOptionValue);
        }
        return copy;
      },
      set(value) {
        const values = value.filter((v) => v !== this.otherOptionValue);
        this.setMultiChoiceValue({
          value: values,
          id: this.extendedUserProfileField.id,
        });
        this.v$.value.$touch();
      },
    },
    other: {
      get() {
        return this.getMultiChoiceOther(this.extendedUserProfileField.id);
      },
      set(value) {
        this.setMultiChoiceOther({
          value,
          id: this.extendedUserProfileField.id,
        });
        this.v$.other.$touch();
      },
    },
    showOther() {
      return this.other || this.otherOptionSelected;
    },
    options() {
      return this.extendedUserProfileField &&
        this.extendedUserProfileField.choices
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
      value: {
        required: requiredIf(() => this.required),
      },
      other: {},
    };
    if (this.showOther) {
      validations.other = { required };
    }
    return validations;
  },
  methods: {
    ...mapMutations("extendedUserProfile", [
      "setMultiChoiceValue",
      "setMultiChoiceOther",
    ]),
    onChange(event) {
      const checked = event.target.checked;
      const val = event.target.value;
      // handle other option toggle
      if (val === String(this.otherOptionValue)) {
        this.otherOptionSelected = checked;
        if (!checked) {
          this.other = "";
        }
      }
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
