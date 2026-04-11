<template>
  <div class="modal fade" ref="modal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">New SSH Credential</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label">Description <span class="text-danger">*</span></label>
            <input class="form-control" type="text" placeholder="Description" required
              v-model="description" @keydown.enter="okClicked" ref="descInput" />
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
  name: "new-ssh-credential-modal",
  data() {
    return {
      description: null,
    };
  },
  computed: {
    valid() {
      return this.description != null && this.description.trim() !== "";
    },
  },
  methods: {
    okClicked() {
      if (!this.valid) return;
      this.$emit("new", { description: this.description });
      Modal.getInstance(this.$refs.modal).hide();
      this.description = null;
    },
    show() {
      this.description = null;
      new Modal(this.$refs.modal).show();
      this.$nextTick(() => {
        if (this.$refs.descInput) this.$refs.descInput.focus();
      });
    },
  },
};
</script>
