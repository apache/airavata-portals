<template>
  <div class="inline-block">
    <a
      href="#"
      class="inline-flex cursor-pointer items-center gap-1 whitespace-nowrap text-destructive hover:underline"
      @click.prevent="$refs.modal.show()"
    >
      Delete
      <Trash2 class="size-4" aria-hidden="true" />
    </a>
    <confirmation-dialog ref="modal" :title="dialogTitle" @ok="$emit('delete')">
      <slot></slot>
    </confirmation-dialog>
  </div>
</template>

<script>
import { Trash2 } from "@lucide/vue";
import ConfirmationDialog from "./ConfirmationDialog.vue";

export default {
  name: "delete-link",
  components: {
    Trash2,
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
