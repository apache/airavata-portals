<template>
  <extended-user-profile-value-editor v-bind="$props">
    <div>
      <div v-for="option in options" :key="option.value" class="form-check">
        <input
          v-model="value"
          :class="[
            'form-check-input',
            validateStateErrorOnly(v$.value) === false ? 'is-invalid' : '',
          ]"
          type="checkbox"
          :value="option.value"
          @change="onChange"
        />
        <label class="form-check-label">{{ option.text }}</label>
      </div>
      <div v-if="extendedUserProfileField.other" class="form-check">
        <input
          v-model="value"
          class="form-check-input"
          type="checkbox"
          :value="otherOptionValue"
          @change="onChange"
        />
        <label class="form-check-label">Other (please specify)</label>
      </div>
      <div v-if="v$.value.$dirty && v$.value.$error" class="invalid-feedback d-block">
        This field is required.
      </div>
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

const other = computed<string | null>({
  get: () => userStore.getMultiChoiceOther(props.extendedUserProfileField.id!),
  set: (val) => {
    userStore.setMultiChoiceOther({
      value: val ?? "",
      id: props.extendedUserProfileField.id!,
    });
    v$.value.other.$touch();
  },
});

const showOther = computed(() => !!other.value || otherOptionSelected.value);

const value = computed<Array<string | object>>({
  get: () => {
    const copy: Array<string | object> = userStore
      .getMultiChoiceValue(props.extendedUserProfileField.id!)
      .slice();
    if (showOther.value) {
      copy.push(otherOptionValue);
    }
    return copy;
  },
  set: (val) => {
    const values = (val as Array<string | object>).filter((v) => v !== otherOptionValue) as string[];
    userStore.setMultiChoiceValue({
      value: values,
      id: props.extendedUserProfileField.id!,
    });
    v$.value.value.$touch();
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
  const validations: Record<string, object> = {
    value: { required: requiredIf(() => isRequired.value) },
    other: {},
  };
  if (showOther.value) {
    validations.other = { required };
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
  const target = event.target as HTMLInputElement;
  const checked = target.checked;
  const val = target.value;
  // handle other option toggle
  if (val === String(otherOptionValue)) {
    otherOptionSelected.value = checked;
    if (!checked) {
      other.value = "";
    }
  }
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
