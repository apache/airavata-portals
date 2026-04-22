<template>
  <div class="delete-link">
    <button
      type="button"
      class="btn btn-outline-danger btn-pill"
      :disabled="disabled"
      @click="modal?.show()"
    >
      <i class="fa fa-trash me-1" aria-hidden="true"></i>Delete
    </button>
    <confirmation-dialog ref="modal" :title="dialogTitle" @ok="emit('delete')">
      <slot></slot>
    </confirmation-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ConfirmationDialog from "./ConfirmationDialog.vue";

withDefaults(defineProps<{
  dialogTitle?: string;
  disabled?: boolean;
}>(), {
  dialogTitle: "Please confirm delete",
  disabled: false,
});

const emit = defineEmits<{
  delete: [];
}>();

const modal = ref<InstanceType<typeof ConfirmationDialog> | null>(null);
</script>

<style scoped>
.delete-link {
  display: inline-block;
}
</style>
