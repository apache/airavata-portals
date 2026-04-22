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

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useVuelidate } from "@vuelidate/core";
import { required, requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
import type { ExtendedUserProfileField } from "django-airavata-common-ui/js/types/user";
import ExtendedUserProfileValueEditor from "./ExtendedUserProfileValueEditor.vue";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const OTHER_OPTION = new Object(); // sentinel value

const props = defineProps<{ extendedUserProfileField: ExtendedUserProfileField }>();
const emit = defineEmits<{ valid: []; invalid: [] }>();

const userStore = useUserStore();
const otherOptionSelected = ref(false);

const isRequired = computed(() => props.extendedUserProfileField.required);
const otherOptionValue = OTHER_OPTION;

const showOther = computed(() => {
  const storeValue = userStore.getSingleChoiceValue(props.extendedUserProfileField.id!);
  return (storeValue === null && !!other.value) || otherOptionSelected.value;
});

const value = computed<object | string | null>({
  get: () => showOther.value ? otherOptionValue : userStore.getSingleChoiceValue(props.extendedUserProfileField.id!),
  set: (val) => {
    if (val !== otherOptionValue) {
      userStore.setSingleChoiceValue({
        value: val as string,
        id: props.extendedUserProfileField.id!,
      });
      v$.value.value.$touch();
    }
  },
});

const other = computed<string | null>({
  get: () => userStore.getSingleChoiceOther(props.extendedUserProfileField.id!),
  set: (val) => {
    userStore.setSingleChoiceOther({
      value: val ?? "",
      id: props.extendedUserProfileField.id!,
    });
    v$.value.other.$touch();
  },
});

const options = computed(() =>
  props.extendedUserProfileField?.choices
    ? props.extendedUserProfileField.choices.map((choice) => ({
        value: choice.id,
        text: choice.display_text,
      }))
    : [],
);

const rules = computed(() => {
  const validations: Record<string, object> = { value: {}, other: {} };
  if (showOther.value) {
    validations.other = { required };
  } else {
    validations.value = { required: requiredIf(() => isRequired.value) };
  }
  return validations;
});

const formState = computed(() => ({
  value: value.value,
  other: other.value,
}));

const v$ = useVuelidate(rules, formState);

const valid = computed(() => !v$.value.$invalid);

const validateState = errors.vuelidateHelpers.validateState;
const validateStateErrorOnly = errors.vuelidateHelpers.validateStateErrorOnly;

watch(
  valid,
  (isValid) => {
    if (isValid) emit("valid");
    else emit("invalid");
  },
  { immediate: true },
);

function onChange(event: Event): void {
  const target = event.target as HTMLSelectElement;
  otherOptionSelected.value = target.value === String(otherOptionValue);
}

function onInput(): void {
  otherOptionSelected.value = true;
}

function touch(): void {
  v$.value.$touch();
}

defineExpose({ touch });
</script>

<style></style>
