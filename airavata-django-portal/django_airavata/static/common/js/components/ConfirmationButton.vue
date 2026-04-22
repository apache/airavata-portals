<template>
  <div class="confirmation-button">
    <button :class="['btn', 'btn-' + variant]" :disabled="disabled" @click="modal?.show()">
      {{ label }}
    </button>
    <confirmation-dialog ref="modal" :title="dialogTitle" @ok="emit('confirmed')">
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
  variant?: string;
}>(), {
  dialogTitle: "Please confirm",
  disabled: false,
  label: "Update",
  variant: "danger",
});

const emit = defineEmits<{
  confirmed: [];
}>();

const modal = ref<InstanceType<typeof ConfirmationDialog> | null>(null);
</script>

<style scoped>
.confirmation-button {
  display: inline-block;
}
</style>
