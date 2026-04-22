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

<script setup lang="ts">
import { ref, computed, nextTick } from "vue";
import { Modal } from "bootstrap";

const emit = defineEmits<{
  new: [data: { username: string; password: string; description: string }];
}>();

const modal = ref<HTMLElement | null>(null);
const usernameInput = ref<HTMLInputElement | null>(null);
const username = ref<string | null>(null);
const password = ref<string | null>(null);
const description = ref<string | null>(null);

const valid = computed(
  () =>
    username.value &&
    username.value.trim() !== "" &&
    password.value &&
    password.value.trim() !== "" &&
    description.value &&
    description.value.trim() !== "",
);

function okClicked() {
  if (!valid.value || !username.value || !password.value || !description.value) return;
  emit("new", {
    username: username.value,
    password: password.value,
    description: description.value,
  });
  if (modal.value) Modal.getInstance(modal.value)?.hide();
  username.value = null;
  password.value = null;
  description.value = null;
}

function show() {
  username.value = null;
  password.value = null;
  description.value = null;
  if (modal.value) new Modal(modal.value).show();
  nextTick(() => {
    usernameInput.value?.focus();
  });
}

defineExpose({ show });
</script>
