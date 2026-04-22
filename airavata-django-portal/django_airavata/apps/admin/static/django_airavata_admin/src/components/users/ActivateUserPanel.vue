<template>
  <div class="card" header="Activate User">
    <p class="card-text">
      User {{ username }} has verified their email address, but doesn't yet have an Airavata User
      Profile. Click <b>Activate</b>
      to create an Airavata User Profile for this user. This will allow the user to be assigned to
      groups.
    </p>
    <button class="btn" @click="activate">Activate</button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  username: string;
}>();

const emit = defineEmits<{
  "activate-user": [username: string];
}>();

function activate() {
  emit("activate-user", props.username);
}
</script>
