<template>
  <div v-if="user">
    <form-group
      label="Username"
      :disabled="true"
      description="Only administrators can update a username."
    >
      <input v-model="user.username" class="form-control" />
    </form-group>
    <div class="mb-3" :disabled="disabled">
      <label class="form-label">First Name</label>
      <input
        v-model="v$.first_name.$model"
        :class="['form-control', validateState(v$.first_name) === false ? 'is-invalid' : '']"
        @keydown.enter="save"
      />
    </div>
    <div class="mb-3" :disabled="disabled">
      <label class="form-label">Last Name</label>
      <input
        v-model="v$.last_name.$model"
        :class="['form-control', validateState(v$.last_name) === false ? 'is-invalid' : '']"
        @keydown.enter="save"
      />
    </div>
    <div class="mb-3" :disabled="disabled">
      <label class="form-label">Email</label>
      <input
        v-model="v$.email.$model"
        :class="['form-control', validateState(v$.email) === false ? 'is-invalid' : '']"
        @keydown.enter="save"
      />
      <div v-if="v$.email.$dirty && v$.email.email.$invalid" class="invalid-feedback">
        {{ email }} is not a valid email address.
      </div>
      <div v-if="user.pending_email_change" class="alert alert-warning mt-1">
        Once you verify your email address at
        <strong>{{ user.pending_email_change.email_address }}</strong
        >, your email address will be updated. If you didn't receive the verification email,
        <a @click="$emit('resend-email-verification')">click here to resend verification link.</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, watch } from "vue";
import { storeToRefs } from "pinia";
import { errors } from "django-airavata-common-ui";
import { useVuelidate } from "@vuelidate/core";
import { email as emailValidator, required } from "@vuelidate/validators";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const props = withDefaults(defineProps<{ disabled?: boolean }>(), { disabled: false });
const emit = defineEmits<{ save: []; "resend-email-verification": [] }>();

const userStore = useUserStore();
const { user } = storeToRefs(userStore);

// Local reactive state keeps vuelidate $model writes in sync with the store.
const formState = reactive({ first_name: "", last_name: "", email: "" });

// Sync store → local state whenever user changes
watch(
  user,
  (u) => {
    if (u) {
      formState.first_name = u.first_name;
      formState.last_name = u.last_name;
      formState.email = u.email;
    }
  },
  { immediate: true },
);

// Sync local state writes → store (called by vuelidate $model setter via the watch below)
watch(() => formState.first_name, (first_name) => userStore.setUserFirstName({ first_name }));
watch(() => formState.last_name, (last_name) => userStore.setUserLastName({ last_name }));
watch(() => formState.email, (email) => userStore.setUserEmail({ email }));

const rules = {
  first_name: { required },
  last_name: { required },
  email: { required, email: emailValidator },
};

const v$ = useVuelidate(rules, formState);

onMounted(() => {
  if (!props.disabled) {
    v$.value.$touch();
  }
});

const valid = computed(() => !v$.value.$invalid);
const email = computed(() => formState.email);
const validateState = errors.vuelidateHelpers.validateState;

function save(): void {
  emit("save");
}

defineExpose({ valid });
</script>

<style></style>
