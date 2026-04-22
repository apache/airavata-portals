<template>
  <div class="card">
    <div class="card-header">Change Username</div>
    <div class="card-body">
      <p class="card-text">
        This will change the user's username in the identity service. Typically, you would only
        change the user's username when they login through an external identity provider and are
        automatically assigned an invalid username. Also, after updating the username the user will
        need to log out and log back in.
      </p>
      <div v-if="airavataUserProfileExists" class="alert alert-warning">
        This user already has an Airavata User Profile. Giving the user a new username will result
        in the user getting a new Airavata User Profile and losing the old one and everything
        (projects, experiments, etc.) associated with it.
      </div>
      <div class="mb-3">
        <label class="form-label">New Username</label>
        <div class="input-group">
          <input
            id="new-username"
            v-model="v$.newUsername.$model"
            :class="['form-control', validateState(v$.newUsername) === false ? 'is-invalid' : '']"
          />
          <span class="input-group-text">
            <button class="btn" @click="newUsername = email">Copy Email Address</button>
          </span>
        </div>
        <div
          v-if="
            v$.newUsername.$dirty &&
            v$.newUsername.emailOrMatchesRegex &&
            v$.newUsername.emailOrMatchesRegex.$invalid
          "
          class="invalid-feedback d-block"
        >
          Username can only contain lowercase letters, numbers, underscores and hyphens OR it can be
          the same as the email address.
        </div>
      </div>
      <confirmation-button
        variant="primary"
        :disabled="v$.$invalid || username === newUsername"
        dialog-title="Please confirm username change"
        @confirmed="updateUsername"
      >
        Please confirm that you want to change the user's username to
        <strong>{{ newUsername }}</strong
        >. After updating the username the user will need to log out and log back in.
        <div v-if="airavataUserProfileExists" class="alert alert-danger">
          This user already has an Airavata User Profile. Giving the user a new username will result
          in the user getting a new Airavata User Profile and
          <strong
            >losing the old one and everything (projects, experiments, etc.) associated with
            it</strong
          >.
        </div>
      </confirmation-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { components, errors } from "django-airavata-common-ui";
import { useVuelidate } from "@vuelidate/core";
import { helpers, or, required, sameAs } from "@vuelidate/validators";

const ConfirmationButton = components.ConfirmationButton;

const props = defineProps<{
  username: string;
  email: string;
  airavataUserProfileExists?: boolean;
}>();

const emit = defineEmits<{
  "update-username": [pair: [string, string]];
}>();

const newUsername = ref<string>(props.username);

const usernameRegex = helpers.regex(/^[a-z0-9_-]+$/);
const emailOrMatchesRegex = or(usernameRegex, sameAs(computed(() => props.email)));

const rules = computed(() => ({
  newUsername: {
    required,
    emailOrMatchesRegex,
  },
}));

const state = computed(() => ({ newUsername: newUsername.value }));
const v$ = useVuelidate(rules, state);

const validateState = errors.vuelidateHelpers.validateState;

function updateUsername() {
  if (!v$.value.$invalid) {
    emit("update-username", [props.username, newUsername.value]);
  }
}
</script>
