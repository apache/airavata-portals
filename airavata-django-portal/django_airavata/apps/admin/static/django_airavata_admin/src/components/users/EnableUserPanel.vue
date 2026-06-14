<template>
  <Card>
    <CardHeader>
      <CardTitle>Enable User</CardTitle>
    </CardHeader>
    <CardContent>
      <p class="mb-4">
        Enable user {{ username }} to log in. By clicking <b>Enable</b> you are
        verifying that the user's email address is {{ email }}
      </p>
      <Button @click="enable">Enable</Button>
    </CardContent>
  </Card>
</template>

<script>
export default {
  name: "enable-user-panel",
  props: {
    username: {
      type: String,
      required: true,
    },
    email: {
      type: String,
      required: true,
    },
  },
  methods: {
    enable() {
      this.$emit("enable-user", this.username);
    },
  },
};
</script>
