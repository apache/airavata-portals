<template>
  <div class="delete-link">
    <a class="text-danger action-link" @click="$refs.modal.show()">
      Delete
      <i class="fa fa-trash" aria-hidden="true"></i>
    </a>
    <confirmation-dialog ref="modal" :title="dialogTitle" @ok="$emit('delete')">
      <slot></slot>
    </confirmation-dialog>
  </div>
</template>

<script>
import ConfirmationDialog from "./ConfirmationDialog.vue";

export default {
  name: "delete-link",
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
  components: {
    ConfirmationDialog,
  },
};
</script>

<style scoped>
.delete-link {
  display: inline-block;
}
</style>
