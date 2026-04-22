<template>
  <div class="card">
    <div class="card-header">User Profile</div>
    <div class="card-body p-0">
      <table class="table table-sm table-borderless mb-0">
        <thead>
          <tr>
            <th>name</th>
            <th>value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.name">
            <td>{{ item.name }}</td>
            <td>
              <i v-if="item.valid" class="fas fa-check text-success"></i>
              <i v-if="!item.valid" class="fas fa-times text-danger"></i>
              {{ item.value }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { models } from "django-airavata-api";

const props = defineProps<{
  iamUserProfile: InstanceType<typeof models.IAMUserProfile>;
}>();

function isValid(fieldName: string) {
  return props.iamUserProfile.user_profile_invalid_fields.indexOf(fieldName) < 0;
}

const items = computed(() => {
  if (!props.iamUserProfile) return [];
  return [
    { name: "Username", value: props.iamUserProfile.user_id, valid: isValid("username") },
    { name: "Email", value: props.iamUserProfile.email, valid: isValid("email") },
    { name: "First Name", value: props.iamUserProfile.first_name, valid: isValid("first_name") },
    { name: "Last Name", value: props.iamUserProfile.last_name, valid: isValid("last_name") },
  ];
});
</script>

<style></style>
