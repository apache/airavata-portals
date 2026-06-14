<template>
  <Card>
    <CardHeader>
      <CardTitle>Details</CardTitle>
    </CardHeader>
    <CardContent class="space-y-1 text-sm">
      <div><b>Name: </b>{{ name }}</div>
      <div><b>Email: </b>{{ userProfile.email }}</div>

      <div class="flex items-center gap-2">
        <span v-if="role"><b>Role: </b></span>
        <Select
          v-if="isOwner && role !== 'OWNER'"
          :model-value="role"
          @update:model-value="changeRole($event)"
        >
          <SelectTrigger class="w-40">
            <SelectValue placeholder="Select role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem
              v-for="option in groupRoleOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.text }}
            </SelectItem>
          </SelectContent>
        </Select>
        <span v-if="(!isOwner && role) || (isOwner && role == 'OWNER')">{{
          role
        }}</span>
      </div>
    </CardContent>
  </Card>
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
