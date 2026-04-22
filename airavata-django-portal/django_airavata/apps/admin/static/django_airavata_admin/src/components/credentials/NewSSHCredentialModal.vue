<template>
  <div ref="modal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">New SSH Credential</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label">Description <span class="text-danger">*</span></label>
            <input
              ref="descInput"
              v-model="description"
              class="form-control"
              type="text"
              placeholder="Description"
              required
              @keydown.enter="okClicked"
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

<script setup lang="ts">
import { ref, computed, nextTick } from "vue";
import { Modal } from "bootstrap";

const emit = defineEmits<{
  new: [data: { description: string }];
}>();

const modal = ref<HTMLElement | null>(null);
const descInput = ref<HTMLInputElement | null>(null);
const description = ref<string | null>(null);

const valid = computed(
  // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
  () => description.value != null && description.value.trim() !== "",
);

function okClicked() {
  if (!valid.value || !description.value) return;
  emit("new", { description: description.value });
  if (modal.value) Modal.getInstance(modal.value)?.hide();
  description.value = null;
}

function show() {
  description.value = null;
  if (modal.value) new Modal(modal.value).show();
  nextTick(() => {
    descInput.value?.focus();
  });
}

defineExpose({ show });
</script>
