<template>
  <Dialog v-model:open="open">
    <DialogContent :show-close-button="false">
      <DialogHeader>
        <DialogTitle>{{ title }}</DialogTitle>
      </DialogHeader>
      <div class="text-sm">
        <slot></slot>
      </div>
      <DialogFooter>
        <Button variant="outline" @click="cancel">Cancel</Button>
        <Button variant="destructive" @click="confirm">Confirm</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script>
export default {
  name: "confirmation-dialog",
  props: {
    title: {
      type: String,
      default: "Please confirm",
    },
  },
  data() {
    return {
      open: false,
    };
  },
  methods: {
    show() {
      this.open = true;
    },
    hide() {
      this.open = false;
    },
    confirm() {
      this.open = false;
      this.$emit("ok");
    },
    cancel() {
      this.open = false;
      this.$emit("cancel");
    },
  },
};
</script>
