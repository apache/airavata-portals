<template>
  <div class="modal fade" ref="modal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">New Password Credential</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label">Username <span class="text-danger">*</span></label>
            <input class="form-control" type="text" placeholder="Username" required v-model="username" ref="usernameInput" />
          </div>
          <div class="mb-3">
            <label class="form-label">Password <span class="text-danger">*</span></label>
            <input class="form-control" type="password" placeholder="Password" required v-model="password" />
          </div>
          <div class="mb-3">
            <label class="form-label">Description <span class="text-danger">*</span></label>
            <input class="form-control" type="text" placeholder="Description" required v-model="description" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
          <button class="btn btn-primary btn-sm" @click="okClicked" :disabled="!valid">Create</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from "bootstrap";

export default {
  name: "new-password-credential-modal",
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
