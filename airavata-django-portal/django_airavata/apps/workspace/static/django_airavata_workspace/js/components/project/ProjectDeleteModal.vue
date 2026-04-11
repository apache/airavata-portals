<template>
  <div class="modal fade" ref="modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Delete Project</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="error" class="alert alert-danger">{{ error }}</div>
          <p>
            Deleting <strong>{{ projectName }}</strong> will permanently delete
            all experiments, datasets, and associated data within this project.
            This cannot be undone.
          </p>
          <div class="mb-3">
            <label class="form-label">Type the project name to confirm:</label>
            <input
              type="text"
              class="form-control"
              v-model="confirmName"
              :placeholder="projectName"
              @keydown.enter="handleDelete"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
          <button
            type="button"
            class="btn btn-danger btn-sm"
            :disabled="confirmName !== projectName || deleting"
            @click="handleDelete"
          >
            <i v-if="deleting" class="fa fa-spinner fa-spin me-1"></i>
            Delete Project
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from "bootstrap";

export default {
  name: "project-delete-modal",
  props: {
    projectId: { type: String, required: true },
    projectName: { type: String, required: true },
  },
  emits: ["delete"],
  data() {
    return {
      confirmName: "",
      deleting: false,
      error: null,
      bsModal: null,
    };
  },
  methods: {
    show() {
      this.confirmName = "";
      this.error = null;
      this.deleting = false;
      if (!this.bsModal) {
        this.bsModal = new Modal(this.$refs.modal);
      }
      this.bsModal.show();
    },
    hide() {
      if (this.bsModal) {
        this.bsModal.hide();
      }
    },
    handleDelete() {
      if (this.confirmName !== this.projectName || this.deleting) return;
      this.deleting = true;
      this.error = null;
      this.$emit("delete", this.projectId);
    },
  },
  beforeUnmount() {
    if (this.bsModal) {
      this.bsModal.dispose();
    }
  },
};
</script>
