<template>
  <div
    ref="modal"
    class="modal fade"
    tabindex="-1"
    data-bs-backdrop="static"
    data-bs-keyboard="false"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ title }}</h5>
        </div>
        <div class="modal-body">
          <slot></slot>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" @click="cancel">Cancel</button>
          <button class="btn btn-primary btn-sm" @click="ok">Confirm</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Modal } from "bootstrap";

withDefaults(defineProps<{
  title?: string;
}>(), {
  title: "Please confirm",
});

const emit = defineEmits<{
  ok: [];
  cancel: [];
}>();

const modal = ref<HTMLElement | null>(null);

function show(): void {
  new Modal(modal.value!).show();
}

function hide(): void {
  const instance = Modal.getInstance(modal.value!);
  if (instance) instance.hide();
}

function ok(): void {
  emit("ok");
  hide();
}

function cancel(): void {
  emit("cancel");
  hide();
}

defineExpose({ show, hide });
</script>
