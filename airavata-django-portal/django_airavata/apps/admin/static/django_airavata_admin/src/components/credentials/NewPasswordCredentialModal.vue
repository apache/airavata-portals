<template>
  <div ref="modal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">New Password Credential</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label">Username <span class="text-danger">*</span></label>
            <input
              ref="usernameInput"
              v-model="username"
              class="form-control"
              type="text"
              placeholder="Username"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Password <span class="text-danger">*</span></label>
            <input
              v-model="password"
              class="form-control"
              type="password"
              placeholder="Password"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Description <span class="text-danger">*</span></label>
            <input
              v-model="description"
              class="form-control"
              type="text"
              placeholder="Description"
              required
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
          <button class="btn btn-primary btn-sm" :disabled="!valid" @click="okClicked">
            Create
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from "bootstrap";

export default {
  name: "NewPasswordCredentialModal",
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
      if (!this.valid) return;
      this.$emit("new", {
        username: this.username,
        password: this.password,
        description: this.description,
      });
      Modal.getInstance(this.$refs.modal).hide();
      this.username = null;
      this.password = null;
      this.description = null;
    },
    show() {
      this.username = null;
      this.password = null;
      this.description = null;
      new Modal(this.$refs.modal).show();
      this.$nextTick(() => {
        if (this.$refs.usernameInput) this.$refs.usernameInput.focus();
      });
    },
  },
};
</script>
