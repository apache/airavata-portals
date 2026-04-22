<template>
  <div class="delete-button">
    <button class="btn btn-danger btn-sm" :disabled="disabled" @click="modal?.show()">
      {{ label }}
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
  label?: string;
}>(), {
  dialogTitle: "Please confirm delete",
  disabled: false,
  label: "Delete",
});

const emit = defineEmits<{
  delete: [];
}>();

const modal = ref<InstanceType<typeof ConfirmationDialog> | null>(null);
</script>

<style scoped>
.delete-button {
  display: inline-block;
}
</style>
