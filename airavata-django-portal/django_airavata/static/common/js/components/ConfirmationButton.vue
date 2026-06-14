<template>
  <div class="inline-block">
    <Button :variant="buttonVariant" @click="$refs.modal.show()" :disabled="disabled">
      {{ label }}
    </Button>
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

// Map the legacy bootstrap-vue variant names this component still accepts onto
// the shadcn-vue Button variants.
const VARIANT_MAP = {
  danger: "destructive",
  primary: "default",
  secondary: "secondary",
  "outline-primary": "outline",
  "outline-secondary": "outline",
  link: "link",
};

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
  computed: {
    buttonVariant() {
      return VARIANT_MAP[this.variant] || this.variant;
    },
  },
};
</script>
