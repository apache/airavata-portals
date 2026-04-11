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
            {{ slotProps.suggestion.user.firstName }}
            {{ slotProps.suggestion.user.lastName }} ({{
              slotProps.suggestion.user.userId
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
        <tr v-for="item in sortedUserPermissions" :key="item.user.airavataInternalUserId">
          <td>
            <span
              :title="item.user.userId"
              :class="userDataClasses"
              v-if="!isPermissionReadOnly(item.permissionType)"
              >{{ item.user.firstName }} {{ item.user.lastName }}</span
            >
            <span v-else class="text-muted fst-italic"
              >{{ item.user.firstName }} {{ item.user.lastName }}</span
            >
          </td>
          <td>
            <span
              :class="userDataClasses"
              v-if="!isPermissionReadOnly(item.permissionType)"
              >{{ item.user.email }}</span
            >
            <span v-else class="text-muted fst-italic">{{ item.user.email }}</span>
          </td>
          <td>
            <select class="form-select form-select-sm"
              v-if="!isPermissionReadOnly(item.permissionType)"
              v-model="item.permissionType"
            >
              <option v-for="opt in permissionOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
            </select>
            <span
              v-else
              class="text-uppercase text-muted fst-italic"
              :class="userDataClasses"
              >{{ item.permissionType.name }}</span
            >
          </td>
          <td>
            <a
              v-if="!isPermissionReadOnly(item.permissionType)"
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
            <span v-if="editingAllowed(item.group, item.permissionType)">{{ item.group.name }}</span>
            <span v-else class="text-muted fst-italic">{{ item.group.name }}</span>
          </td>
          <td>
            <select class="form-select form-select-sm"
              v-if="editingAllowed(item.group, item.permissionType)"
              v-model="item.permissionType"
            >
              <option v-for="opt in permissionOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
            </select>
            <span v-else class="text-muted fst-italic">{{ item.permissionType.name }}</span>
          </td>
          <td>
            <a
              v-if="editingAllowed(item.group, item.permissionType)"
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
      return this.data && this.data.userPermissions
        ? this.data.userPermissions.length
        : 0;
    },
    sortedUserPermissions: function () {
      const userPermsCopy = this.data.userPermissions
        ? this.data.userPermissions.slice()
        : [];
      const sortedUserPerms = utils.StringUtils.sortIgnoreCase(
        userPermsCopy,
        (userPerm) => userPerm.user.lastName + ", " + userPerm.user.firstName
      );
      // When in readonly mode, if the current owner isn't the owner, display
      // the user with the OWNER permission
      if (this.readonly && !this.data.isOwner) {
        sortedUserPerms.push(
          new models.UserPermission({
            user: this.data.owner,
            permissionType: models.ResourcePermissionType.OWNER,
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
      return this.data && this.data.groupPermissions
        ? this.data.groupPermissions
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
      if (this.data.isOwner || this.data.isOwner === null) {
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
      const currentUserIds = this.data.userPermissions
        ? this.data.userPermissions.map(
            (userPerm) => userPerm.user.airavataInternalUserId
          )
        : [];
      return this.users
        .filter(
          (user) => currentUserIds.indexOf(user.airavataInternalUserId) < 0
        )
        .filter(
          (user) =>
            user.airavataInternalUserId !==
            session.Session.airavataInternalUserId
        )
        .map((user) => {
          return {
            id: user.airavataInternalUserId,
            name:
              user.firstName +
              " " +
              user.lastName +
              " (" +
              user.userId +
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
          (user) => user.airavataInternalUserId === suggestion.id
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
          !this.data.isOwner &&
          permission === models.ResourcePermissionType.MANAGE_SHARING
        )
      );
    },
    isPermissionReadOnly: function (permission) {
      // if it is a new entity, it will not be readonly
      if (this.data.isOwner == null) {
        return false;
      }
      return (
        !this.data.isOwner &&
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
