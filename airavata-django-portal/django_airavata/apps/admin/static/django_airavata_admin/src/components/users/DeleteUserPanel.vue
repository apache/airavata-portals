<template>
  <div class="card" header="Delete User">
    <p class="card-text">This will remove {{ username }} from the identity service.</p>
    <delete-button @delete="deleteUser">
      Are you sure you want to delete <strong>{{ username }}</strong
      >?
    </delete-button>
  </div>
</template>

<script setup lang="ts">
import { components } from "django-airavata-common-ui";

const DeleteButton = components.DeleteButton;

const props = defineProps<{
  username: string;
}>();

const emit = defineEmits<{
  "delete-user": [username: string];
}>();

function deleteUser() {
  emit("delete-user", props.username);
}
</script>
