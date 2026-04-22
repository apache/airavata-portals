<template>
  <span :class="['badge', 'bg-' + variant]">{{ name }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Group {
  is_gateway_admins_group?: boolean;
  is_read_only_gateway_admins_group?: boolean;
  is_default_gateway_users_group?: boolean;
  name?: string;
  [key: string]: unknown;
}

const props = defineProps<{
  group: Group;
}>();

const variant = computed(() => {
  if (props.group.is_gateway_admins_group) {
    return "danger";
  } else if (props.group.is_read_only_gateway_admins_group) {
    return "warning";
  } else if (props.group.is_default_gateway_users_group) {
    return "primary";
  } else {
    return "secondary";
  }
});

const name = computed(() => {
  if (props.group.is_gateway_admins_group) {
    return "Admins";
  } else if (props.group.is_read_only_gateway_admins_group) {
    return "Read Only Admins";
  } else if (props.group.is_default_gateway_users_group) {
    return "Default";
  } else {
    return props.group.name;
  }
});
</script>
