<template>
<div>
    <div class="card">
      <div class="card-header">Details</div>
      <div class="card-body">
        <b>Name: </b> {{name}}<br>
        <b>Email: </b> {{userProfile.email}}<br>

        <span v-if="role"><b>Role: </b></span>
        <select class="form-select"
            v-if="isOwner && role !== 'OWNER'"
            :value="role"
            @input="changeRole($event)"
          >
          <option v-for="opt in groupRoleOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
        </select>
        <span v-if="(!isOwner && role) || (isOwner && role=='OWNER')">{{ role }}</span>
      </div>
    </div>
    
</div>
</template>

<script>

import { models } from "django-airavata-api";
//GroupMembersDetailsContainer
export default {
 name: "group-members-details-container",
  props: {
    userProfile: {
      type: models.userProfile,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    role: {
      type: String,
      required: false,
    },
    isOwner: {
      type: Boolean,
      required: false,
      default: false,
    },
    id: {
      type: String,
      required: true,
    },
  },
  
  methods: {
    changeRole(role) {
      this.$emit("change-role", [this.id, role]);
    },
  },
  computed: {
    groupRoleOptions() {
      return [
        {
          value: "MEMBER",
          text: "MEMBER",
        },
        {
          value: "ADMIN",
          text: "ADMIN",
        },
      ];
    },
  },
};
</script>