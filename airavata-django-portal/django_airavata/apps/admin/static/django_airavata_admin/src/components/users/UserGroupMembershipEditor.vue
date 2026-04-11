<template>
  <div class="mb-3">
    <label class="form-label">Groups</label>
    <div
      v-if="gatewayUsersGroupOption"
      class="form-check"
    >
      <input
        class="form-check-input"
        type="checkbox"
        :id="'group-' + gatewayUsersGroupOption.value"
        :value="gatewayUsersGroupOption.value"
        :checked="selected.includes(gatewayUsersGroupOption.value)"
        :disabled="gatewayUsersGroupOption.disabled"
        @change="toggleGroup(gatewayUsersGroupOption.value, $event.target.checked)"
      />
      <label class="form-check-label" :for="'group-' + gatewayUsersGroupOption.value">
        {{ gatewayUsersGroupOption.text }}
        <gateway-groups-badge :group="gatewayUsersGroup" />
      </label>
    </div>
    <div
      v-if="adminsGroupOption"
      class="form-check"
    >
      <input
        class="form-check-input"
        type="checkbox"
        :id="'group-' + adminsGroupOption.value"
        :value="adminsGroupOption.value"
        :checked="selected.includes(adminsGroupOption.value)"
        :disabled="adminsGroupOption.disabled"
        @change="toggleGroup(adminsGroupOption.value, $event.target.checked)"
      />
      <label class="form-check-label" :for="'group-' + adminsGroupOption.value">
        {{ adminsGroupOption.text }}
        <gateway-groups-badge :group="adminsGroup" />
      </label>
    </div>
    <div
      v-if="readOnlyAdminsGroupOption"
      class="form-check"
    >
      <input
        class="form-check-input"
        type="checkbox"
        :id="'group-' + readOnlyAdminsGroupOption.value"
        :value="readOnlyAdminsGroupOption.value"
        :checked="selected.includes(readOnlyAdminsGroupOption.value)"
        :disabled="readOnlyAdminsGroupOption.disabled"
        @change="toggleGroup(readOnlyAdminsGroupOption.value, $event.target.checked)"
      />
      <label class="form-check-label" :for="'group-' + readOnlyAdminsGroupOption.value">
        {{ readOnlyAdminsGroupOption.text }}
        <gateway-groups-badge :group="readOnlyAdminsGroup" />
      </label>
    </div>
    <div
      v-for="option in userDefinedGroupOptions"
      :key="option.value"
      class="form-check"
    >
      <input
        class="form-check-input"
        type="checkbox"
        :id="'group-' + option.value"
        :value="option.value"
        :checked="selected.includes(option.value)"
        :disabled="option.disabled"
        @change="toggleGroup(option.value, $event.target.checked)"
      />
      <label class="form-check-label" :for="'group-' + option.value">{{ option.text }}</label>
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
        this.createGroupOption(g)
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
      return this.combinedGroups.find((g) => g.is_read_only_gateway_admins_group);
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
          !group.user_has_write_access ||
          group.ownerId === this.airavata_internal_user_id,
      };
    },
  },
};
</script>
