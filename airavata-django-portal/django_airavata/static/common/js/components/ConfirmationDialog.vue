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

<script>
import { Modal } from "bootstrap";

export default {
  name: "ConfirmationDialog",
  props: {
    title: {
      type: String,
      default: "Please confirm",
    },
  },
  methods: {
    show() {
      new Modal(this.$refs.modal).show();
    },
    hide() {
      const instance = Modal.getInstance(this.$refs.modal);
      if (instance) instance.hide();
    },
    ok() {
      this.$emit("ok");
      this.hide();
    },
    cancel() {
      this.$emit("cancel");
      this.hide();
    },
  },
};
</script>
