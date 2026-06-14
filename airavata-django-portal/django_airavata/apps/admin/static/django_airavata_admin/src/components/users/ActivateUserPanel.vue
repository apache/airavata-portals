<template>
  <Card>
    <CardHeader>
      <CardTitle>Activate User</CardTitle>
    </CardHeader>
    <CardContent>
      <p class="mb-4">
        User {{ username }} has verified their email address, but doesn't yet
        have an Airavata User Profile. Click <b>Activate</b>
        to create an Airavata User Profile for this user. This will allow the
        user to be assigned to groups.
      </p>
      <Button @click="activate">Activate</Button>
    </CardContent>
  </Card>
</template>

<script>
export default {
  name: "activate-user-panel",
  props: {
    username: {
      type: String,
      required: true,
    },
  },
  methods: {
    activate() {
      this.$emit("activate-user", this.username);
    },
  },
};
</script>
