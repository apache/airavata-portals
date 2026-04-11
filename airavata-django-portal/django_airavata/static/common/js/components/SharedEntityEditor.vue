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
          <span v-if="slotProps.suggestion.type == 'user'">
            <i class="fa fa-user"></i>
            {{ slotProps.suggestion.user.first_name }}
            {{ slotProps.suggestion.user.last_name }} ({{
              slotProps.suggestion.user.user_id
            }}) - {{ slotProps.suggestion.user.email }}
          </span>
        </template>
      </autocomplete-text-input>
    </div>
    <h5 v-if="totalCount > 0">
      <slot name="permissions-header">Currently Shared With</slot>
    </h5>
    <table class="table" v-if="usersCount > 0" id="modal-user-table">
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
              :title="item.user.user_id"
              :class="userDataClasses"
              v-if="!isPermissionReadOnly(item.permission_type)"
              >{{ item.user.first_name }} {{ item.user.last_name }}</span
            >
            <span v-else class="text-muted fst-italic"
              >{{ item.user.first_name }} {{ item.user.last_name }}</span
            >
          </td>
          <td>
            <span
              :class="userDataClasses"
              v-if="!isPermissionReadOnly(item.permission_type)"
              >{{ item.user.email }}</span
            >
            <span v-else class="text-muted fst-italic">{{ item.user.email }}</span>
          </td>
          <td>
            <select class="form-select form-select-sm"
              v-if="!isPermissionReadOnly(item.permission_type)"
              v-model="item.permission_type"
            >
              <option v-for="opt in permissionOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
            </select>
            <span
              v-else
              class="text-uppercase text-muted fst-italic"
              :class="userDataClasses"
              >{{ item.permission_type.name }}</span
            >
          </td>
          <td>
            <a
              v-if="!isPermissionReadOnly(item.permission_type)"
              @click="removeUser(item.user)"
              role="button"
            >
              <span class="fa fa-trash"></span>
            </a>
          </td>
        </tr>
      </tbody>
    </table>
    <table class="table" v-if="groupsCount > 0" id="modal-group-table">
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
            <span v-if="editingAllowed(item.group, item.permission_type)">{{ item.group.name }}</span>
            <span v-else class="text-muted fst-italic">{{ item.group.name }}</span>
          </td>
          <td>
            <select class="form-select form-select-sm"
              v-if="editingAllowed(item.group, item.permission_type)"
              v-model="item.permission_type"
            >
              <option v-for="opt in permissionOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
            </select>
            <span v-else class="text-muted fst-italic">{{ item.permission_type.name }}</span>
          </td>
          <td>
            <a
              v-if="editingAllowed(item.group, item.permission_type)"
              @click="removeGroup(item.group)"
              role="button"
            >
              <span class="fa fa-trash"></span>
            </a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { models, utils, session } from "django-airavata-api";
import AutocompleteTextInput from "./AutocompleteTextInput.vue";
import VModelMixin from "../mixins/VModelMixin";

export default {
  name: "shared-entity-editor",
  mixins: [VModelMixin],
  props: {
    modelValue: {
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
  },
  computed: {
    userFields: function () {
      return [
        { key: "name", label: "User Name", class: "text-truncate" },
        { key: "email", label: "Email", class: "text-truncate" },
        { key: "permission", label: "Permission" },
        { key: "remove", label: "Remove" },
      ];
    },
    groupFields: function () {
      return [
        { key: "name", label: "Group Name" },
        { key: "permission", label: "Permission" },
        { key: "remove", label: "Remove" },
      ];
    },
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
        "text-muted": this.readonly,
        "font-italic": this.readonly,
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
          (user) =>
            user.airavata_internal_user_id !==
            session.Session.airavata_internal_user_id
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

<style scoped>
#modal-user-table {
  table-layout: fixed;
}
</style>
