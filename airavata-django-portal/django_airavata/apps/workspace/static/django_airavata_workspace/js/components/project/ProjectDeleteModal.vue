<template>
  <div ref="modal" class="modal fade" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Delete Project</h5>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div v-if="error" class="alert alert-danger">{{ error }}</div>
          <p>
            Deleting <strong>{{ projectName }}</strong> will permanently delete all experiments,
            datasets, and associated data within this project. This cannot be undone.
          </p>
          <div class="mb-3">
            <label class="form-label">Type the project name to confirm:</label>
            <input
              v-model="confirmName"
              type="text"
              class="form-control"
              :placeholder="projectName"
              @keydown.enter="handleDelete"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">
            Cancel
          </button>
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

<script setup lang="ts">
import { ref, onBeforeUnmount } from "vue";
import { Modal } from "bootstrap";

const props = defineProps<{
  projectId: string;
  projectName: string;
}>();

const emit = defineEmits<{
  delete: [projectId: string];
}>();

const modal = ref<HTMLElement | null>(null);
const confirmName = ref("");
const deleting = ref(false);
const error = ref<string | null>(null);
const bsModal = ref<Modal | null>(null);

onBeforeUnmount(() => {
  bsModal.value?.dispose();
});

function show() {
  confirmName.value = "";
  error.value = null;
  deleting.value = false;
  if (!bsModal.value && modal.value) {
    bsModal.value = new Modal(modal.value);
  }
  bsModal.value?.show();
}

function hide() {
  bsModal.value?.hide();
}

function handleDelete() {
  if (confirmName.value !== props.projectName || deleting.value) return;
  deleting.value = true;
  error.value = null;
  emit("delete", props.projectId);
}

defineExpose({ show, hide });
</script>
