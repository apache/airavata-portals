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

<script>
import { models } from "django-airavata-api";
export default {
  props: {
    iamUserProfile: {
      type: models.IAMUserProfile,
      required: true,
    },
  },
  computed: {
    fields() {
      return ["name", "value"];
    },
    items() {
      if (!this.iamUserProfile) {
        return [];
      } else {
        return [
          {
            name: "Username",
            value: this.iamUserProfile.user_id,
            valid: this.isValid("username"),
          },
          {
            name: "Email",
            value: this.iamUserProfile.email,
            valid: this.isValid("email"),
          },
          {
            name: "First Name",
            value: this.iamUserProfile.first_name,
            valid: this.isValid("first_name"),
          },
          {
            name: "Last Name",
            value: this.iamUserProfile.last_name,
            valid: this.isValid("last_name"),
          },
        ];
      }
    },
  },
  methods: {
    isValid(fieldName) {
      return (
        this.iamUserProfile.user_profile_invalid_fields.indexOf(fieldName) < 0
      );
    },
  },
};
</script>

<style></style>
