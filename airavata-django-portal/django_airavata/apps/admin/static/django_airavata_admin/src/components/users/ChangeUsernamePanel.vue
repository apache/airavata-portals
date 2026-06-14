<template>
  <Card>
    <CardHeader>
      <CardTitle>Change Username</CardTitle>
    </CardHeader>
    <CardContent>
      <p class="mb-4">
        This will change the user's username in the identity service. Typically,
        you would only change the user's username when they login through an
        external identity provider and are automatically assigned an invalid
        username. Also, after updating the username the user will need to log
        out and log back in.
      </p>
      <Alert
        v-if="airavataUserProfileExists"
        class="mb-4 border-transparent bg-warning text-warning-foreground"
      >
        <AlertDescription class="text-warning-foreground">
          This user already has an Airavata User Profile. Giving the user a new
          username will result in the user getting a new Airavata User Profile
          and losing the old one and everything (projects, experiments, etc.)
          associated with it.
        </AlertDescription>
      </Alert>
      <div class="space-y-1.5">
        <Label for="new-username">New Username</Label>
        <div class="flex items-stretch gap-2">
          <Input
            id="new-username"
            v-model="v$.newUsername.$model"
            :aria-invalid="validateState(v$.newUsername) === false"
          />
          <Button variant="outline" @click="newUsername = email"
            >Copy Email Address</Button
          >
        </div>
        <p
          v-if="
            validateState(v$.newUsername) === false &&
            v$.newUsername.emailOrMatchesRegex.$invalid
          "
          class="text-sm text-destructive"
        >
          Username can only contain lowercase letters, numbers, underscores and
          hyphens OR it can be the same as the email address.
        </p>
      </div>
      <confirmation-button
        class="mt-4"
        variant="default"
        @confirmed="updateUsername"
        :disabled="v$.$invalid || username === newUsername"
        dialog-title="Please confirm username change"
      >
        Please confirm that you want to change the user's username to
        <strong>{{ newUsername }}</strong
        >. After updating the username the user will need to log out and log
        back in.
        <Alert
          v-if="airavataUserProfileExists"
          variant="destructive"
          class="mt-2"
        >
          <AlertDescription>
            This user already has an Airavata User Profile. Giving the user a
            new username will result in the user getting a new Airavata User
            Profile and
            <strong
              >losing the old one and everything (projects, experiments, etc.)
              associated with it</strong
            >.
          </AlertDescription>
        </Alert>
      </confirmation-button>
    </CardContent>
  </Card>
</template>

<script>
import { components, errors } from "django-airavata-common-ui";
import { useVuelidate } from "@vuelidate/core";
import { helpers, or, required, sameAs } from "@vuelidate/validators";
export default {
  name: "change-username-panel",
  setup() {
    return { v$: useVuelidate() };
  },
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
  data() {
    return {
      newUsername: this.username,
    };
  },
  validations() {
    // @vuelidate/validators 2: helpers.regex takes just the regexp, and sameAs
    // compares against a value (was a sibling-field name in vuelidate 0.x).
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
