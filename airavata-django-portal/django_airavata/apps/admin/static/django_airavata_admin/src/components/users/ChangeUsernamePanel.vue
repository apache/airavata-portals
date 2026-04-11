<template>
  <div class="card">
    <div class="card-header">Change Username</div>
    <div class="card-body">
      <p class="card-text">
        This will change the user's username in the identity service. Typically,
        you would only change the user's username when they login through an
        external identity provider and are automatically assigned an invalid
        username. Also, after updating the username the user will need to log out
        and log back in.
      </p>
      <div class="alert alert-warning" v-if="airavataUserProfileExists">
        This user already has an Airavata User Profile. Giving the user a new
        username will result in the user getting a new Airavata User Profile and
        losing the old one and everything (projects, experiments, etc.) associated
        with it.
      </div>
      <div class="mb-3">
        <label class="form-label">New Username</label>
        <div class="input-group">
          <input :class="['form-control', validateState(v$.newUsername) === false ? 'is-invalid' : '']"
            id="new-username"
            v-model="v$.newUsername.$model"
          />
          <span class="input-group-text">
            <button class="btn" @click="newUsername = email">Copy Email Address</button>
          </span>
        </div>
        <div class="invalid-feedback d-block"
          v-if="v$.newUsername.$dirty && v$.newUsername.emailOrMatchesRegex && v$.newUsername.emailOrMatchesRegex.$invalid"
        >
          Username can only contain lowercase letters, numbers, underscores and
          hyphens OR it can be the same as the email address.
        </div>
      </div>
      <confirmation-button
        variant="primary"
        @confirmed="updateUsername"
        :disabled="v$.$invalid || username === newUsername"
        dialog-title="Please confirm username change"
      >
        Please confirm that you want to change the user's username to
        <strong>{{ newUsername }}</strong
        >. After updating the username the user will need to log out and log back
        in.
        <div class="alert alert-danger" v-if="airavataUserProfileExists">
          This user already has an Airavata User Profile. Giving the user a new
          username will result in the user getting a new Airavata User Profile and
          <strong
            >losing the old one and everything (projects, experiments, etc.)
            associated with it</strong
          >.
        </div>
      </confirmation-button>
    </div>
  </div>
</template>

<script>
import { components, errors } from "django-airavata-common-ui";
import { useVuelidate } from "@vuelidate/core";
import { helpers, or, required, sameAs } from "@vuelidate/validators";
export default {
  name: "change-username-panel",
  props: {
    username: {
      type: String,
      required: true,
    },
    email: {
      type: String,
      required: true,
    },
    airavataUserProfileExists: {
      type: Boolean,
      default: false,
    },
  },
  components: {
    "confirmation-button": components.ConfirmationButton,
  },
  setup() {
    return { v$: useVuelidate() };
  },
  data() {
    return {
      newUsername: this.username,
    };
  },
  validations() {
    const usernameRegex = helpers.regex(/^[a-z0-9_-]+$/);
    const emailOrMatchesRegex = or(usernameRegex, sameAs(this.email));
    return {
      newUsername: {
        required,
        emailOrMatchesRegex,
      },
    };
  },
  methods: {
    updateUsername() {
      if (!this.v$.$invalid) {
        this.$emit("update-username", [this.username, this.newUsername]);
      }
    },
    validateState: errors.vuelidateHelpers.validateState,
  },
};
</script>
