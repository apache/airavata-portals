<template>
  <!-- TODO: migrate to Bootstrap 5 modal --><div class="modal"
    title="New Password Credential"
    ref="modal"
    @ok="okClicked"
    ok-title="Create"
    :ok-disabled="!valid"
  >
    <input class="form-control"
      type="text"
      placeholder="Username"
      required
      v-model="username"
    />
    <input class="form-control"
      type="password"
      placeholder="Password"
      required
      v-model="password"
    />
    <input class="form-control"
      type="text"
      placeholder="Description"
      required
      v-model="description"
    />
  </div>
</template>

<script>
export default {
  name: "new-ssh-credential-modal",
  data() {
    return {
      username: null,
      password: null,
      description: null,
    };
  },
  computed: {
    valid() {
      return (
        this.username &&
        this.username.trim() !== "" &&
        this.password &&
        this.password.trim() !== "" &&
        this.description &&
        this.description.trim() !== ""
      );
    },
  },
  methods: {
    okClicked() {
      this.$emit("new", {
        username: this.username,
        password: this.password,
        description: this.description,
      });
    },
    show() {
      this.$refs.modal.show();
    },
  },
};
</script>
