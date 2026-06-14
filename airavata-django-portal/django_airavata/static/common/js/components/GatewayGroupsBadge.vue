<template>
  <Badge :variant="variant" :class="badgeClass">{{ name }}</Badge>
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
        return "destructive";
      } else if (this.group.is_default_gateway_users_group) {
        return "default";
      } else {
        return "secondary";
      }
    },
    badgeClass() {
      // warning has no dedicated Badge variant; apply the design-token color.
      return this.group.is_read_only_gateway_admins_group
        ? "border-transparent bg-warning text-warning-foreground"
        : "";
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
