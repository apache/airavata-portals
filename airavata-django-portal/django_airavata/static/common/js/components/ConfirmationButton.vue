<template>
  <div class="confirmation-button">
    <button :class="['btn', 'btn-' + variant]" :disabled="disabled" @click="$refs.modal.show()">
      {{ label }}
    </button>
    <confirmation-dialog ref="modal" :title="dialogTitle" @ok="$emit('confirmed')">
      <slot></slot>
    </confirmation-dialog>
  </div>
</template>
<script>
import ConfirmationDialog from "./ConfirmationDialog.vue";

export default {
  name: "ConfirmationButton",
  components: {
    ConfirmationDialog,
  },
  props: {
    dialogTitle: {
      type: String,
      default: "Please confirm",
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    label: {
      type: String,
      default: "Update",
    },
    variant: {
      type: String,
      default: "danger",
    },
  },
};
</script>

<style scoped>
.confirmation-button {
  display: inline-block;
}
</style>
