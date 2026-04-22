<template>
  <div>
    <div v-if="!readonly" class="mb-3">
      <label for="user-groups-autocomplete" class="form-label">Search for users/groups</label>
      <autocomplete-text-input
        id="user-groups-autocomplete"
        :suggestions="usersAndGroupsSuggestions"
        @selected="suggestionSelected"
      >
        <template #suggestion="slotProps">
          <span v-if="slotProps.suggestion.type == 'group'">
            <i class="fa fa-users"></i> {{ slotProps.suggestion.name }}
          </span>
          <span v-if="slotProps.suggestion.type == 'user' && slotProps.suggestion.user">
            <i class="fa fa-user"></i>
            {{ slotProps.suggestion.user.first_name }}
            {{ slotProps.suggestion.user.last_name }} ({{ slotProps.suggestion.user.user_id }}) -
            {{ slotProps.suggestion.user.email }}
          </span>
        </template>
      </autocomplete-text-input>
    </div>
    <h5 v-if="totalCount > 0">
      <slot name="permissions-header">Currently Shared With</slot>
    </h5>
    <table v-if="usersCount > 0" id="modal-user-table" class="table">
      <thead>
        <tr>
          <th>User Name</th>
          <th>Email</th>
          <th>Permission</th>
          <th>Remove</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sortedUserPermissions" :key="item.user.airavata_internal_user_id">
          <td>
            <span
              v-if="!isPermissionReadOnly(item.permission_type)"
              :title="item.user.user_id"
              :class="userDataClasses"
              >{{ item.user.first_name }} {{ item.user.last_name }}</span
            >
            <span v-else class="text-muted fst-italic"
              >{{ item.user.first_name }} {{ item.user.last_name }}</span
            >
          </td>
          <td>
            <span v-if="!isPermissionReadOnly(item.permission_type)" :class="userDataClasses">{{
              item.user.email
            }}</span>
            <span v-else class="text-muted fst-italic">{{ item.user.email }}</span>
          </td>
          <td>
            <select
              v-if="!isPermissionReadOnly(item.permission_type)"
              v-model="item.permission_type"
              class="form-select form-select-sm"
            >
              <option v-for="opt in permissionOptions" :key="opt.value" :value="opt.value">
                {{ opt.text }}
              </option>
            </select>
            <span v-else class="text-uppercase text-muted fst-italic" :class="userDataClasses">{{
              item.permission_type.name
            }}</span>
          </td>
          <td>
            <a
              v-if="!isPermissionReadOnly(item.permission_type)"
              role="button"
              @click="removeUser(item.user)"
            >
              <span class="fa fa-trash"></span>
            </a>
          </td>
        </tr>
      </tbody>
    </table>
    <table v-if="groupsCount > 0" id="modal-group-table" class="table">
      <thead>
        <tr>
          <th>Group Name</th>
          <th>Permission</th>
          <th>Remove</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sortedGroupPermissions" :key="item.group.id">
          <td>
            <span v-if="editingAllowed(item.group, item.permission_type)">{{
              item.group.name
            }}</span>
            <span v-else class="text-muted fst-italic">{{ item.group.name }}</span>
          </td>
          <td>
            <select
              v-if="editingAllowed(item.group, item.permission_type)"
              v-model="item.permission_type"
              class="form-select form-select-sm"
            >
              <option v-for="opt in permissionOptions" :key="opt.value" :value="opt.value">
                {{ opt.text }}
              </option>
            </select>
            <span v-else class="text-muted fst-italic">{{ item.permission_type.name }}</span>
          </td>
          <td>
            <a
              v-if="editingAllowed(item.group, item.permission_type)"
              role="button"
              @click="removeGroup(item.group)"
            >
              <span class="fa fa-trash"></span>
            </a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { models, utils, session } from "django-airavata-api";
import AutocompleteTextInput from "./AutocompleteTextInput.vue";

interface Suggestion {
  id: string | number;
  name: string;
  type?: string;
  user?: {
    first_name?: string;
    last_name?: string;
    user_id?: string;
    email?: string;
    airavata_internal_user_id?: unknown;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

// VModelMixin inlined: copies modelValue to local `data`, watches for changes and emits update:modelValue
function copyValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => copyValue(item));
  } else {
    if (value === null || value === undefined) {
      return null;
    } else if (value instanceof (models.BaseModel as new (..._args: unknown[]) => { clone(): unknown })) {
      return value.clone();
    } else if (typeof value === "object") {
      return JSON.parse(JSON.stringify(value));
    } else {
      return value;
    }
  }
}

const props = withDefaults(defineProps<{
  modelValue?: InstanceType<typeof models.SharedEntity> | null;
  users: unknown[];
  groups: unknown[];
  disallowEditingAdminGroups?: boolean;
  readonly?: boolean;
}>(), {
  modelValue: null,
  disallowEditingAdminGroups: true,
  readonly: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: InstanceType<typeof models.SharedEntity>];
}>();

// VModelMixin: local data copy of modelValue
const data = ref(copyValue(props.modelValue) as InstanceType<typeof models.SharedEntity> | null);

// VModelMixin watch: deep watch data, emit update:modelValue on change
watch(
  data,
  (newValue, oldValue) => {
    if (typeof props.modelValue === "object" && newValue === oldValue) {
      emit("update:modelValue", newValue as InstanceType<typeof models.SharedEntity>);
    } else if (
      (props.modelValue === null || typeof props.modelValue !== "object") &&
      newValue !== oldValue
    ) {
      emit("update:modelValue", newValue as InstanceType<typeof models.SharedEntity>);
    }
  },
  { deep: true },
);

// VModelMixin watch: when modelValue changes, re-clone into data
watch(
  () => props.modelValue,
  (newValue) => {
    data.value = copyValue(newValue) as InstanceType<typeof models.SharedEntity> | null;
  },
  { deep: true },
);

const usersCount = computed(() =>
  data.value && data.value.user_permissions ? data.value.user_permissions.length : 0,
);

const sortedUserPermissions = computed(() => {
  const userPermsCopy = data.value?.user_permissions ? data.value.user_permissions.slice() : [];
  const sortedUserPerms = utils.StringUtils.sortIgnoreCase(
    userPermsCopy,
    (userPerm: { user: { last_name: string; first_name: string } }) =>
      userPerm.user.last_name + ", " + userPerm.user.first_name,
  );
  // When in readonly mode, if the current owner isn't the owner, display
  // the user with the OWNER permission
  if (props.readonly && data.value && !data.value.is_owner) {
    sortedUserPerms.push(
      new models.UserPermission({
        user: data.value.owner,
        permission_type: models.ResourcePermissionType.OWNER,
      }),
    );
  }
  return sortedUserPerms;
});

const userDataClasses = computed(() => ({
  "text-muted": props.readonly,
  "font-italic": props.readonly,
}));

const filteredGroupPermissions = computed(() =>
  data.value && data.value.group_permissions ? data.value.group_permissions : [],
);

const sortedGroupPermissions = computed(() => {
  const groupPermsCopy = filteredGroupPermissions.value.slice();
  // Sort by name, then admin groups should come last if editing is disallowed
  utils.StringUtils.sortIgnoreCase(
    groupPermsCopy,
    (g: { group: { name: string } }) => g.group.name,
  );
  if (props.disallowEditingAdminGroups) {
    groupPermsCopy.sort((a: { group: { isAdminGroup?: boolean } }, b: { group: { isAdminGroup?: boolean } }) => {
      if (a.group.isAdminGroup && !b.group.isAdminGroup) {
        return 1;
      }
      return 0;
    });
  }
  return groupPermsCopy;
});

const groupsCount = computed(() => filteredGroupPermissions.value.length);
const totalCount = computed(() => usersCount.value + groupsCount.value);

const permissionOptions = computed(() => {
  const options = [models.ResourcePermissionType.READ, models.ResourcePermissionType.WRITE];
  // manage_sharing permission is visible only if the user is the owner or it is a new entity and owner is not defined
  if (data.value && (data.value.is_owner || data.value.is_owner === null)) {
    options.push(models.ResourcePermissionType.MANAGE_SHARING);
  }
  return options.map((perm) => ({
    value: perm,
    text: perm.name,
  }));
});

const groupSuggestions = computed(() => {
  // filter out already selected groups
  const currentGroupIds = filteredGroupPermissions.value.map(
    (groupPerm: { group: { id: unknown } }) => groupPerm.group.id,
  );
  return (props.groups as { id: unknown; name: string; isAdminGroup?: boolean }[])
    .filter((group) => currentGroupIds.indexOf(group.id) < 0)
    .filter((group) => {
      // Filter out admin groups from options
      if (props.disallowEditingAdminGroups) {
        return !group.isAdminGroup;
      } else {
        return true;
      }
    })
    .map((group) => ({
      id: group.id as string | number,
      name: group.name,
      type: "group" as const,
    }));
});

const userSuggestions = computed(() => {
  // filter out already selected users
  const currentUserIds = data.value?.user_permissions
    ? data.value.user_permissions.map(
        (userPerm: { user: { airavata_internal_user_id: unknown } }) =>
          userPerm.user.airavata_internal_user_id,
      )
    : [];
  return (
    props.users as {
      airavata_internal_user_id: unknown;
      first_name: string;
      last_name: string;
      user_id: string;
      email: string;
    }[]
  )
    .filter((user) => currentUserIds.indexOf(user.airavata_internal_user_id) < 0)
    .filter(
      (user) => user.airavata_internal_user_id !== session.Session.airavata_internal_user_id,
    )
    .map((user) => ({
      id: user.airavata_internal_user_id as string | number,
      name:
        user.first_name + " " + user.last_name + " (" + user.user_id + ") " + user.email,
      user: user,
      type: "user" as const,
    }));
});

const usersAndGroupsSuggestions = computed((): Suggestion[] =>
  (userSuggestions.value as Suggestion[]).concat(groupSuggestions.value as Suggestion[]),
);

function removeUser(user: unknown): void {
  data.value?.removeUser(user);
}

function removeGroup(group: unknown): void {
  data.value?.removeGroup(group);
}

function suggestionSelected(suggestion: Suggestion): void {
  if (suggestion.type === "group") {
    const group = (props.groups as { id: unknown }[]).find((g) => g.id === suggestion.id);
    data.value?.addGroup({ group });
  } else if (suggestion.type === "user") {
    const user = (props.users as { airavata_internal_user_id: unknown }[]).find(
      (u) => u.airavata_internal_user_id === suggestion.id,
    );
    data.value?.addUser(user);
  }
}

/**
 * For some entity types the backend automatically shares the entity with
 * admin users and doesn't allow editing or removing those admin groups.
 * For that reason the disallowEditingAdminGroups property was added and
 * when it is true editing of the "Admins" and "Read Only Admins" groups
 * should not be allowed.
 */
function editingAllowed(group: { isAdminGroup?: boolean }, permission: unknown): boolean {
  return (
    !props.readonly &&
    (!props.disallowEditingAdminGroups || !group.isAdminGroup) &&
    !(data.value && !data.value.is_owner && permission === models.ResourcePermissionType.MANAGE_SHARING)
  );
}

function isPermissionReadOnly(permission: unknown): boolean {
  // if it is a new entity, it will not be readonly
  // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
  if (data.value == null || data.value.is_owner == null) {
    return false;
  }
  return !data.value.is_owner && permission === models.ResourcePermissionType.MANAGE_SHARING;
}
</script>

<style scoped>
#modal-user-table {
  table-layout: fixed;
}
</style>
