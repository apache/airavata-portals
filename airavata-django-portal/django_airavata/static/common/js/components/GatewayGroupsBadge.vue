<template>
  <b-badge :variant="variant">{{ name }}</b-badge>
</template>

<script>
import { models } from "django-airavata-api";

export default {
  name: "gateway-groups-badge",
  props: {
    group: {
      type: models.Group,
      required: true,
    },
  },
  computed: {
    variant() {
      if (this.group.is_gateway_admins_group) {
        return "danger";
      } else if (this.group.is_read_only_gateway_admins_group) {
        return "warning";
      } else if (this.group.is_default_gateway_users_group) {
        return "primary";
      } else {
        return "secondary";
      }
    },
    name() {
      if (this.group.is_gateway_admins_group) {
        return "Admins";
      } else if (this.group.is_read_only_gateway_admins_group) {
        return "Read Only Admins";
      } else if (this.group.is_default_gateway_users_group) {
        return "Default";
      } else {
        return this.group.name;
      }
    },
  },
};
</script>
