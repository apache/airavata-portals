<template>
  <div class="confirmation-button">
    <button class="btn"
      :variant="variant"
      @click="$refs.modal.show()"
      :disabled="disabled"
    >
      {{ label }}
    </button>
    <confirmation-dialog
      ref="modal"
      :title="dialogTitle"
      @ok="$emit('confirmed')"
    >
      <slot></slot>
    </confirmation-dialog>
  </div>
</template>
<script>
import ConfirmationDialog from "./ConfirmationDialog.vue";

export default {
  name: "confirmation-button",
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
  components: {
    ConfirmationDialog,
  },
};
</script>

<style scoped>
.confirmation-button {
  display: inline-block;
}
</style>
