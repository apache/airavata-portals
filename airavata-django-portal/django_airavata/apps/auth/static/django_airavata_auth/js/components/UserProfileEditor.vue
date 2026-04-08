<template>
  <div v-if="user">
    <form-group
      label="Username"
      :disabled="true"
      description="Only administrators can update a username."
    >
      <input class="form-control" v-model="user.username" />
    </div>
    <div class="mb-3" label="First Name" :disabled="disabled">
      <input class="form-control"
        v-model="$v.first_name.$model"
        @keydown.enter="save"
        :state="validateState($v.first_name)"
      />
    </div>
    <div class="mb-3" label="Last Name" :disabled="disabled">
      <input class="form-control"
        v-model="$v.last_name.$model"
        @keydown.enter="save"
        :state="validateState($v.last_name)"
      />
    </div>
    <div class="mb-3" label="Email" :disabled="disabled">
      <input class="form-control"
        v-model="$v.email.$model"
        @keydown.enter="save"
        :state="validateState($v.email)"
      />
      <div class="invalid-feedback" v-if="!$v.email.email">
        {{ email }} is not a valid email address.
      </div>
      <div class="alert" class="mt-1" show v-if="user.pending_email_change"
        >Once you verify your email address at
        <strong>{{ user.pending_email_change.email_address }}</strong
        >, your email address will be updated. If you didn't receive the
        verification email,
        <a @click="$emit('resend-email-verification')"
          >click here to resend verification link.</b-link
        ></b-alert
      >
    </div>
  </div>
</template>

<script>
import { errors } from "django-airavata-common-ui";
import { validationMixin } from "vuelidate";
import { email, required } from "vuelidate/lib/validators";
import { mapGetters, mapMutations } from "vuex";

export default {
  name: "user-profile-editor",
  mixins: [validationMixin],
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  created() {
    if (!this.disabled) {
      this.$v.$touch();
    }
  },
  data() {
    return {};
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
      return !this.$v.$invalid;
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
