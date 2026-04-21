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

<script>
import { errors } from "django-airavata-common-ui";
import { useVuelidate } from "@vuelidate/core";
import { email, required } from "@vuelidate/validators";
import { mapGetters, mapMutations } from "vuex";

export default {
  name: "UserProfileEditor",
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  setup() {
    return { v$: useVuelidate() };
  },
  data() {
    return {};
  },
  created() {
    if (!this.disabled) {
      this.v$.$touch();
    }
  },
  computed: {
    ...mapGetters("userProfile", ["user"]),
    first_name: {
      get() {
        return this.user.first_name;
      },
      set(first_name) {
        this.setFirstName({ first_name });
      },
    },
    last_name: {
      get() {
        return this.user.last_name;
      },
      set(last_name) {
        this.setLastName({ last_name });
      },
    },
    email: {
      get() {
        return this.user.email;
      },
      set(email) {
        this.setEmail({ email });
      },
    },
    valid() {
      return !this.v$.$invalid;
    },
  },
  validations() {
    return {
      first_name: {
        required,
      },
      last_name: {
        required,
      },
      email: {
        required,
        email,
      },
    };
  },
  methods: {
    ...mapMutations("userProfile", ["setFirstName", "setLastName", "setEmail"]),
    save() {
      this.$emit("save");
    },
    validateState: errors.vuelidateHelpers.validateState,
  },
};
</script>

<style></style>
