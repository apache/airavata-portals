<template>
  <Card>
    <CardHeader>
      <CardTitle>Delete User</CardTitle>
    </CardHeader>
    <CardContent>
      <p class="mb-4">
        This will remove {{ username }} from the identity service.
      </p>
      <delete-button @delete="deleteUser">
        Are you sure you want to delete <strong>{{ username }}</strong
        >?
      </delete-button>
    </CardContent>
  </Card>
</template>

<script>
import { components } from "django-airavata-common-ui";

export default {
  name: "delete-user-panel",
  props: {
    username: {
      type: String,
      required: true,
    },
  },
  components: {
    "delete-button": components.DeleteButton,
  },
  methods: {
    deleteUser() {
      this.$emit("delete-user", this.username);
    },
  },
};
</script>
