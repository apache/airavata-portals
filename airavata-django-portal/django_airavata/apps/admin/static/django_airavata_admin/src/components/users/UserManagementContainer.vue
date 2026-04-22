<template>
  <div>
    <div class="row">
      <div class="col-auto me-auto">
        <h1 class="h4 mb-4">Manage Users</h1>
      </div>
      <div class="col-auto">
        <button class="btn" :to="{ name: 'extended-user-profile' }">Extended User Profile</button>
      </div>
      <div class="col-auto">
        <div class="dropdown" :text="menuText">
          <a class="dropdown-item" :to="{ name: 'identity-service-users' }" :exact="true"
            >Identity Service</a
          >
          <a class="dropdown-item" :to="{ name: 'unverified-email-users' }" :exact="true"
            >Unverified Emails</a
          >
        </div>
      </div>
    </div>
    <router-view></router-view>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const menuText = computed(() => {
  if (route.name === "identity-service-users") {
    return "Identity Service";
  } else if (route.name === "unverified-email-users") {
    return "Unverified Emails";
  }
  return "Menu";
});
</script>
