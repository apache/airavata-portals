<template>
  <div>
    <div v-if="!readonly" class="space-y-1.5">
      <Label for="user-groups-autocomplete">Search for users/groups</Label>
      <autocomplete-text-input
        id="user-groups-autocomplete"
        :suggestions="usersAndGroupsSuggestions"
        @selected="suggestionSelected"
      >
        <template v-slot:suggestion="slotProps">
          <span
            v-if="slotProps.suggestion.type == 'group'"
            class="flex items-center gap-2"
          >
            <Users class="size-4" /> {{ slotProps.suggestion.name }}
          </span>
          <span
            v-if="slotProps.suggestion.type == 'user'"
            class="flex items-center gap-2"
          >
            <User class="size-4" />
            {{ slotProps.suggestion.user.first_name }}
            {{ slotProps.suggestion.user.last_name }} ({{
              slotProps.suggestion.user.user_id
            }}) - {{ slotProps.suggestion.user.email }}
          </span>
        </template>
      </autocomplete-text-input>
    </div>
    <h5 v-if="totalCount > 0" class="mt-4 text-base font-semibold">
      <slot name="permissions-header">Currently Shared With</slot>
    </h5>
    <Table v-if="usersCount > 0" id="modal-user-table" class="table-fixed">
      <TableHeader>
        <TableRow>
          <TableHead>User Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Permission</TableHead>
          <TableHead>Remove</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow
          v-for="item in sortedUserPermissions"
          :key="item.user.user_id"
        >
          <TableCell class="truncate">
            <span
              :title="item.user.user_id"
              :class="userDataClasses"
              v-if="!isPermissionReadOnly(item.permission_type)"
              >{{ item.user.first_name }} {{ item.user.last_name }}</span
            >
            <span v-else class="italic text-muted-foreground"
              >{{ item.user.first_name }} {{ item.user.last_name }}</span
            >
          </TableCell>
          <TableCell class="truncate">
            <span
              :class="userDataClasses"
              v-if="!isPermissionReadOnly(item.permission_type)"
              >{{ item.user.email }}</span
            >
            <span v-else class="italic text-muted-foreground">{{
              item.user.email
            }}</span>
          </TableCell>
          <TableCell>
            <select
              v-if="!isPermissionReadOnly(item.permission_type)"
              class="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              :value="permissionIndex(item.permission_type)"
              @change="
                item.permission_type = permissionOptions[$event.target.value].value
              "
            >
              <option
                v-for="(option, index) in permissionOptions"
                :key="option.text"
                :value="index"
              >
                {{ option.text }}
              </option>
            </select>
            <span
              v-else
              class="uppercase italic text-muted-foreground"
              :class="userDataClasses"
              >{{ item.permission_type.name }}</span
            >
          </TableCell>
          <TableCell>
            <a
              href="#"
              v-if="!isPermissionReadOnly(item.permission_type)"
              class="inline-flex cursor-pointer text-destructive hover:underline"
              @click.prevent="removeUser(item.user)"
            >
              <Trash2 class="size-4" />
            </a>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
    <Table v-if="groupsCount > 0" id="modal-group-table">
      <TableHeader>
        <TableRow>
          <TableHead>Group Name</TableHead>
          <TableHead>Permission</TableHead>
          <TableHead>Remove</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow
          v-for="item in sortedGroupPermissions"
          :key="item.group.id"
        >
          <TableCell>
            <span
              v-if="editingAllowed(item.group, item.permission_type)"
              >{{ item.group.name }}</span
            >
            <span v-else class="italic text-muted-foreground">{{
              item.group.name
            }}</span>
          </TableCell>
          <TableCell>
            <select
              v-if="editingAllowed(item.group, item.permission_type)"
              class="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              :value="permissionIndex(item.permission_type)"
              @change="
                item.permission_type = permissionOptions[$event.target.value].value
              "
            >
              <option
                v-for="(option, index) in permissionOptions"
                :key="option.text"
                :value="index"
              >
                {{ option.text }}
              </option>
            </select>
            <span v-else class="italic text-muted-foreground">{{
              item.permission_type.name
            }}</span>
          </TableCell>
          <TableCell>
            <a
              href="#"
              v-if="editingAllowed(item.group, item.permission_type)"
              class="inline-flex cursor-pointer text-destructive hover:underline"
              @click.prevent="removeGroup(item.group)"
            >
              <Trash2 class="size-4" />
            </a>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>

<script>
import { Trash2, User, Users } from "@lucide/vue";
import { models, utils, session } from "django-airavata-api";
import AutocompleteTextInput from "./AutocompleteTextInput.vue";
import VModelMixin from "../mixins/VModelMixin";

export default {
  name: "shared-entity-editor",
  mixins: [VModelMixin],
  props: {
    value: {
      type: models.SharedEntity,
    },
    users: {
      type: Array,
      required: true,
    },
    groups: {
      type: Array,
      required: true,
    },
    disallowEditingAdminGroups: {
      type: Boolean,
      default: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  components: {
    AutocompleteTextInput,
    Trash2,
    User,
    Users,
  },
  computed: {
    usersCount: function () {
      return this.data && this.data.user_permissions
        ? this.data.user_permissions.length
        : 0;
    },
    sortedUserPermissions: function () {
      const userPermsCopy = this.data.user_permissions
        ? this.data.user_permissions.slice()
        : [];
      const sortedUserPerms = utils.StringUtils.sortIgnoreCase(
        userPermsCopy,
        (userPerm) => userPerm.user.last_name + ", " + userPerm.user.first_name
      );
      // When in readonly mode, if the current owner isn't the owner, display
      // the user with the OWNER permission
      if (this.readonly && !this.data.is_owner) {
        sortedUserPerms.push(
          new models.UserPermission({
            user: this.data.owner,
            permission_type: models.ResourcePermissionType.OWNER,
          })
        );
      }
      return sortedUserPerms;
    },
    userDataClasses() {
      return {
        "text-muted-foreground": this.readonly,
        italic: this.readonly,
      };
    },
    filteredGroupPermissions: function () {
      return this.data && this.data.group_permissions
        ? this.data.group_permissions
        : [];
    },
    sortedGroupPermissions: function () {
      const groupPermsCopy = this.filteredGroupPermissions.slice();
      // Sort by name, then admin groups should come last if editing is disallowed
      utils.StringUtils.sortIgnoreCase(groupPermsCopy, (g) => g.group.name);
      if (this.disallowEditingAdminGroups) {
        groupPermsCopy.sort((a, b) => {
          if (a.group.isAdminGroup && !b.group.isAdminGroup) {
            return 1;
          }
        });
      }
      return groupPermsCopy;
    },
    groupsCount: function () {
      return this.filteredGroupPermissions.length;
    },
    totalCount: function () {
      return this.usersCount + this.groupsCount;
    },
    permissionOptions: function () {
      var options = [
        models.ResourcePermissionType.READ,
        models.ResourcePermissionType.WRITE,
      ];
      // manage_sharing permission is visible only if the user is the owner or it is a new entity and owner is not defined
      if (this.data.is_owner || this.data.is_owner === null) {
        options.push(models.ResourcePermissionType.MANAGE_SHARING);
      }
      return options.map((perm) => {
        return {
          value: perm,
          text: perm.name,
        };
      });
    },
    groupSuggestions: function () {
      // filter out already selected groups
      const currentGroupIds = this.filteredGroupPermissions.map(
        (groupPerm) => groupPerm.group.id
      );
      return this.groups
        .filter((group) => currentGroupIds.indexOf(group.id) < 0)
        .filter((group) => {
          // Filter out admin groups from options
          if (this.disallowEditingAdminGroups) {
            return !group.isAdminGroup;
          } else {
            return true;
          }
        })
        .map((group) => {
          return {
            id: group.id,
            name: group.name,
            type: "group",
          };
        });
    },
    userSuggestions: function () {
      // filter out already selected users
      const currentUserIds = this.data.user_permissions
        ? this.data.user_permissions.map(
            (userPerm) => userPerm.user.airavata_internal_user_id
          )
        : [];
      return this.users
        .filter(
          (user) => currentUserIds.indexOf(user.airavata_internal_user_id) < 0
        )
        .filter(
          // Session is the portal session object, not a model — its key stays camelCase.
          (user) =>
            user.airavata_internal_user_id !==
            session.Session.airavataInternalUserId
        )
        .map((user) => {
          return {
            id: user.airavata_internal_user_id,
            name:
              user.first_name +
              " " +
              user.last_name +
              " (" +
              user.user_id +
              ") " +
              user.email,
            user: user,
            type: "user",
          };
        });
    },
    usersAndGroupsSuggestions: function () {
      return this.userSuggestions.concat(this.groupSuggestions);
    },
  },
  methods: {
    // Native <select> binds by option index; map the current permission_type
    // (a ResourcePermissionType model instance) to its index in permissionOptions.
    permissionIndex: function (permissionType) {
      const index = this.permissionOptions.findIndex(
        (option) => option.value === permissionType
      );
      return index >= 0 ? index : 0;
    },
    removeUser: function (user) {
      this.data.removeUser(user);
    },
    removeGroup: function (group) {
      this.data.removeGroup(group);
    },
    suggestionSelected: function (suggestion) {
      if (suggestion.type === "group") {
        const group = this.groups.find((group) => group.id === suggestion.id);
        this.data.addGroup({ group });
      } else if (suggestion.type === "user") {
        const user = this.users.find(
          (user) => user.airavata_internal_user_id === suggestion.id
        );
        this.data.addUser(user);
      }
    },
    /**
     * For some entity types the backend automatically shares the entity with
     * admin users and doesn't allow editing or removing those admin groups.
     * For that reason the disallowEditingAdminGroups property was added and
     * when it is true editing of the "Admins" and "Read Only Admins" groups
     * should not be allowed.
     */
    editingAllowed(group, permission) {
      return (
        !this.readonly &&
        (!this.disallowEditingAdminGroups || !group.isAdminGroup) &&
        !(
          !this.data.is_owner &&
          permission === models.ResourcePermissionType.MANAGE_SHARING
        )
      );
    },
    isPermissionReadOnly: function (permission) {
      // if it is a new entity, it will not be readonly
      if (this.data.is_owner == null) {
        return false;
      }
      return (
        !this.data.is_owner &&
        permission === models.ResourcePermissionType.MANAGE_SHARING
      );
    },
  },
};
</script>
