<template>
  <span>
    <gateway-groups-badge v-if="adminsGroup" :group="adminsGroup" />
    <gateway-groups-badge
      v-else-if="readOnlyAdminsGroup"
      :group="readOnlyAdminsGroup"
    />
    <gateway-groups-badge
      v-else-if="defaultUsersGroup"
      :group="defaultUsersGroup"
    />
    <Badge v-for="group in nonGatewayGroups" :key="group.id">{{
      group.name
    }}</Badge>
  </span>
</template>

<script>
import { components } from "django-airavata-common-ui";
export default {
  name: "group-membership-display",
  props: {
    groups: {
      type: Array,
      required: true,
    },
  },
  components: {
    "gateway-groups-badge": components.GatewayGroupsBadge,
  },
  computed: {
    adminsGroup() {
      return this.groups.find((g) => g.is_gateway_admins_group);
    },
    readOnlyAdminsGroup() {
      return this.groups.find((g) => g.is_read_only_gateway_admins_group);
    },
    defaultUsersGroup() {
      return this.groups.find((g) => g.is_default_gateway_users_group);
    },
    nonGatewayGroups() {
      return this.groups.filter((g) => {
        return (
          !g.is_gateway_admins_group &&
          !g.is_read_only_gateway_admins_group &&
          !g.is_default_gateway_users_group
        );
      });
    },
    nonGatewayGroupNames() {
      return this.nonGatewayGroups.map((g) => g.name).join(", ");
    },
  },
};
</script>
