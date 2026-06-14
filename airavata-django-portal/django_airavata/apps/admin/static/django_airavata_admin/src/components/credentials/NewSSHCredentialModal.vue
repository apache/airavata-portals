<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>New SSH Credential</DialogTitle>
      </DialogHeader>
      <div class="space-y-2">
        <Input
          type="text"
          placeholder="Description"
          required
          v-model="description"
        />
      </div>
      <DialogFooter>
        <Button variant="outline" @click="hide">Cancel</Button>
        <Button variant="default" :disabled="!valid" @click="okClicked"
          >Create</Button
        >
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script>
export default {
  name: "new-ssh-credential-modal",
  data() {
    return {
      open: false,
      description: null,
    };
  },
  computed: {
    valid() {
      return this.description != null && this.description.trim() !== "";
    },
  },
  methods: {
    okClicked() {
      this.$emit("new", { description: this.description });
      this.hide();
    },
    show() {
      this.open = true;
    },
    hide() {
      this.open = false;
    },
  },
};
</script>
