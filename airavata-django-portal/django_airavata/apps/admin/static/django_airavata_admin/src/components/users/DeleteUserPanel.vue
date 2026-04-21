<template>
  <div class="card" header="Delete User">
    <p class="card-text">This will remove {{ username }} from the identity service.</p>
    <delete-button @delete="deleteUser">
      Are you sure you want to delete <strong>{{ username }}</strong
      >?
    </delete-button>
  </div>
</template>

<script>
import { components } from "django-airavata-common-ui";

export default {
  name: "DeleteUserPanel",
  components: {
    "delete-button": components.DeleteButton,
  },
  props: {
    username: {
      type: String,
      required: true,
    },
  },
  methods: {
    deleteUser() {
      this.$emit("delete-user", this.username);
    },
  },
};
</script>
