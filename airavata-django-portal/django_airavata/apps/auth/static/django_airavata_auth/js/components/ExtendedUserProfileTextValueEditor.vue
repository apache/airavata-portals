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

<script setup lang="ts">
import { computed, watch } from "vue";
import { useVuelidate } from "@vuelidate/core";
import { requiredIf } from "@vuelidate/validators";
import { errors } from "django-airavata-common-ui";
import type { ExtendedUserProfileField } from "django-airavata-common-ui/js/types/user";
import ExtendedUserProfileValueEditor from "./ExtendedUserProfileValueEditor.vue";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const props = defineProps<{ extendedUserProfileField: ExtendedUserProfileField }>();
const emit = defineEmits<{ valid: []; invalid: [] }>();

const userStore = useUserStore();

const isRequired = computed(() => props.extendedUserProfileField.required);

const value = computed<string | null>({
  get: () => userStore.getTextValue(props.extendedUserProfileField.id!),
  set: (val: string | null) => {
    userStore.setTextValue({ value: val ?? "", id: props.extendedUserProfileField.id! });
    v$.value.$touch();
  },
});

const rules = computed(() => ({
  value: { required: requiredIf(() => isRequired.value) },
}));

const state = computed(() => ({ value: value.value }));
const v$ = useVuelidate(rules, state);

const valid = computed(() => !v$.value.$invalid);
const validateState = errors.vuelidateHelpers.validateState;

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

<style></style>
