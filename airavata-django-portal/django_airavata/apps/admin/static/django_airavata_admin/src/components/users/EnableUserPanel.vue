<template>
  <div class="card" header="Enable User">
    <p class="card-text">
      Enable user {{ username }} to log in. By clicking <b>Enable</b> you are verifying that the
      user's email address is {{ email }}
    </p>
    <button class="btn" @click="enable">Enable</button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  username: string;
  email: string;
}>();

const emit = defineEmits<{
  "enable-user": [username: string];
}>();

function enable() {
  emit("enable-user", props.username);
}
</script>
