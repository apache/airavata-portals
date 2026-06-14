<template>
  <div class="space-y-1.5">
    <Label>Groups</Label>
    <div class="flex flex-col gap-2">
      <label
        v-if="gatewayUsersGroupOption"
        class="flex items-center gap-2 text-sm"
        :class="{
          'cursor-not-allowed opacity-50': gatewayUsersGroupOption.disabled,
        }"
      >
        <Checkbox
          :model-value="selected.includes(gatewayUsersGroupOption.value)"
          :disabled="gatewayUsersGroupOption.disabled"
          @update:model-value="toggleGroup(gatewayUsersGroupOption.value, $event)"
        />
        {{ gatewayUsersGroupOption.text }}
        <gateway-groups-badge :group="gatewayUsersGroup" />
      </label>
      <label
        v-if="adminsGroupOption"
        class="flex items-center gap-2 text-sm"
        :class="{ 'cursor-not-allowed opacity-50': adminsGroupOption.disabled }"
      >
        <Checkbox
          :model-value="selected.includes(adminsGroupOption.value)"
          :disabled="adminsGroupOption.disabled"
          @update:model-value="toggleGroup(adminsGroupOption.value, $event)"
        />
        {{ adminsGroupOption.text }}
        <gateway-groups-badge :group="adminsGroup" />
      </label>
      <label
        v-if="readOnlyAdminsGroupOption"
        class="flex items-center gap-2 text-sm"
        :class="{
          'cursor-not-allowed opacity-50': readOnlyAdminsGroupOption.disabled,
        }"
      >
        <Checkbox
          :model-value="selected.includes(readOnlyAdminsGroupOption.value)"
          :disabled="readOnlyAdminsGroupOption.disabled"
          @update:model-value="
            toggleGroup(readOnlyAdminsGroupOption.value, $event)
          "
        />
        {{ readOnlyAdminsGroupOption.text }}
        <gateway-groups-badge :group="readOnlyAdminsGroup" />
      </label>
      <label
        v-for="option in userDefinedGroupOptions"
        :key="option.value"
        class="flex items-center gap-2 text-sm"
        :class="{ 'cursor-not-allowed opacity-50': option.disabled }"
      >
        <Checkbox
          :model-value="selected.includes(option.value)"
          :disabled="option.disabled"
          @update:model-value="toggleGroup(option.value, $event)"
        />
        {{ option.text }}
      </label>
    </div>
  </div>
</template>

<script>
import { utils } from "django-airavata-api";
import { components, mixins } from "django-airavata-common-ui";
export default {
  name: "user-group-membership-editor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: Array,
      required: true,
    },
    airavataInternalUserId: {
      type: String,
      required: true,
    },
    editableGroups: {
      type: Array,
      required: true,
    },
  },
  components: {
    "gateway-groups-badge": components.GatewayGroupsBadge,
  },
  computed: {
    selected() {
      return this.data.map((g) => g.id);
    },
    combinedGroups() {
      const groups = {};
      this.value.concat(this.editableGroups).forEach((g) => {
        groups[g.id] = g;
      });
      return Object.values(groups);
    },
    userDefinedGroups() {
      return this.combinedGroups
        ? this.combinedGroups.filter((g) => {
            return (
              !g.is_default_gateway_users_group &&
              !g.is_gateway_admins_group &&
              !g.is_read_only_gateway_admins_group
            );
          })
        : [];
    },
    userDefinedGroupOptions() {
      const options = this.userDefinedGroups.map((g) =>
        this.createGroupOption(g),
      );
      return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
    },
    gatewayUsersGroup() {
      return this.combinedGroups.find((g) => g.is_default_gateway_users_group);
    },
    gatewayUsersGroupOption() {
      return this.gatewayUsersGroup
        ? this.createGroupOption(this.gatewayUsersGroup)
        : null;
    },
    adminsGroup() {
      return this.combinedGroups.find((g) => g.is_gateway_admins_group);
    },
    adminsGroupOption() {
      return this.adminsGroup ? this.createGroupOption(this.adminsGroup) : null;
    },
    readOnlyAdminsGroup() {
      return this.combinedGroups.find(
        (g) => g.is_read_only_gateway_admins_group,
      );
    },
    readOnlyAdminsGroupOption() {
      return this.readOnlyAdminsGroup
        ? this.createGroupOption(this.readOnlyAdminsGroup)
        : null;
    },
  },
  methods: {
    toggleGroup(groupId, checked) {
      if (checked) {
        if (!this.data.find((g) => g.id === groupId)) {
          const addedGroup = this.editableGroups.find((g) => g.id === groupId);
          if (addedGroup) {
            this.data.push(addedGroup);
          }
        }
      } else {
        const groupIndex = this.data.findIndex((g) => g.id === groupId);
        if (groupIndex >= 0) {
          this.data.splice(groupIndex, 1);
        }
      }
    },
    createGroupOption(group) {
      return {
        text: group.name,
        value: group.id,
        disabled:
          !group.userHasWriteAccess ||
          group.owner_id === this.airavataInternalUserId,
      };
    },
  },
};
</script>
