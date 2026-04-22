<template>
  <div>
    <button class="btn btn-primary btn-sm" @click="showModal">
      <slot><i class="fa fa-plus me-1"></i>Create New</slot>
    </button>
    <div ref="modal" class="modal fade" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Create New Project</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Project Name <span class="text-danger">*</span></label>
              <input
                ref="nameInput"
                v-model="projectName"
                class="form-control"
                type="text"
                placeholder="Project name"
                @keydown.enter="onCreateProject"
              />
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea
                v-model="projectDescription"
                class="form-control"
                placeholder="Optional description"
                rows="3"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
            <button
              class="btn btn-primary btn-sm"
              :disabled="!projectName || !projectName.trim()"
              @click="onCreateProject"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";
import { models, services } from "django-airavata-api";
import { Modal } from "bootstrap";

const emit = defineEmits<{
  "new-project": [];
}>();

const modal = ref<HTMLElement | null>(null);
const nameInput = ref<HTMLInputElement | null>(null);
const projectName = ref("");
const projectDescription = ref("");

function showModal() {
  projectName.value = "";
  projectDescription.value = "";
  if (modal.value) {
    new Modal(modal.value).show();
  }
  nextTick(() => {
    nameInput.value?.focus();
  });
}

function onCreateProject() {
  if (!projectName.value || !projectName.value.trim()) return;
  const newProject = new models.Project({
    name: projectName.value.trim(),
    description: projectDescription.value,
  });
  services.ProjectService.create({ data: newProject }).then(() => {
    if (modal.value) {
      Modal.getInstance(modal.value)?.hide();
    }
    emit("new-project");
  });
}
</script>
