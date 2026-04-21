<template>
  <div class="delete-link">
    <button
      type="button"
      class="btn btn-outline-danger btn-pill"
      :disabled="disabled"
      @click="$refs.modal.show()"
    >
      <i class="fa fa-trash me-1" aria-hidden="true"></i>Delete
    </button>
    <confirmation-dialog ref="modal" :title="dialogTitle" @ok="$emit('delete')">
      <slot></slot>
    </confirmation-dialog>
  </div>
</template>

<script>
import ConfirmationDialog from "./ConfirmationDialog.vue";

export default {
  name: "DeleteLink",
  components: {
    ConfirmationDialog,
  },
  props: {
    dialogTitle: {
      type: String,
      default: "Please confirm delete",
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
};
</script>

<style scoped>
.delete-link {
  display: inline-block;
}
</style>
