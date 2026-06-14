<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>New Password Credential</DialogTitle>
      </DialogHeader>
      <div class="space-y-2">
        <Input type="text" placeholder="Username" required v-model="username" />
        <Input
          type="password"
          placeholder="Password"
          required
          v-model="password"
        />
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
      username: null,
      password: null,
      description: null,
    };
  },
  computed: {
    valid() {
      return (
        this.username &&
        this.username.trim() !== "" &&
        this.password &&
        this.password.trim() !== "" &&
        this.description &&
        this.description.trim() !== ""
      );
    },
  },
  methods: {
    okClicked() {
      this.$emit("new", {
        username: this.username,
        password: this.password,
        description: this.description,
      });
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
