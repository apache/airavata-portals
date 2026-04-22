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

<script setup lang="ts">
import { computed, watch } from "vue";
import { useVuelidate } from "@vuelidate/core";
import { helpers } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
import type { ExtendedUserProfileField } from "django-airavata-common-ui/js/types/user";
import ExtendedUserProfileValueEditor from "./ExtendedUserProfileValueEditor.vue";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const props = defineProps<{ extendedUserProfileField: ExtendedUserProfileField }>();
const emit = defineEmits<{ valid: []; invalid: [] }>();

const userStore = useUserStore();

const isRequired = computed(() => props.extendedUserProfileField.required);

const value = computed<boolean>({
  get: () => userStore.getUserAgreementValue(props.extendedUserProfileField.id!),
  set: (val: boolean) => {
    userStore.setUserAgreementValue({
      value: val,
      id: props.extendedUserProfileField.id!,
    });
    v$.value.value.$touch();
  },
});

const mustBeTrue = helpers.withParams(
  { type: "mustBeTrue" },
  (val: boolean) => !isRequired.value || val === true,
);

const rules = computed(() => ({
  value: { mustBeTrue },
}));

const formState = computed(() => ({ value: value.value }));
const v$ = useVuelidate(rules, formState);

const valid = computed(() => !v$.value.$invalid);
const validateStateErrorOnly = errors.vuelidateHelpers.validateStateErrorOnly;

watch(
  valid,
  (isValid) => {
    if (isValid) emit("valid");
    else emit("invalid");
  },
  { immediate: true },
);

function touch(): void {
  v$.value.$touch();
}

defineExpose({ touch });
</script>
