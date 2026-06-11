<template>
  <div>
    <b-form-group
      v-if="!readonly"
      label="Search for users/groups"
      labelFor="user-groups-autocomplete"
    >
      <autocomplete-text-input
        id="user-groups-autocomplete"
        :suggestions="usersAndGroupsSuggestions"
        @selected="suggestionSelected"
      >
        <template slot="suggestion" slot-scope="slotProps">
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
    </b-form-group>
    <h5 v-if="totalCount > 0">
      <slot name="permissions-header">Currently Shared With</slot>
    </h5>
    <b-table
      v-if="usersCount > 0"
      id="modal-user-table"
      hover
      :items="sortedUserPermissions"
      :fields="userFields"
    >
      <template slot="cell(name)" slot-scope="data">
        <span
          :title="data.item.user.user_id"
          :class="userDataClasses"
          v-if="!isPermissionReadOnly(data.item.permission_type)"
          >{{ data.item.user.first_name }} {{ data.item.user.last_name }}</span
        >
        <span v-else class="text-muted font-italic"
          >{{ data.item.user.first_name }} {{ data.item.user.last_name }}</span
        >
      </template>
      <template slot="cell(email)" slot-scope="data">
        <span
          :class="userDataClasses"
          v-if="!isPermissionReadOnly(data.item.permission_type)"
          >{{ data.item.user.email }}</span
        >
        <span v-else class="text-muted font-italic">{{
          data.item.user.email
        }}</span>
      </template>
      <template slot="cell(permission)" slot-scope="data">
        <b-form-select
          v-if="!isPermissionReadOnly(data.item.permission_type)"
          v-model="data.item.permission_type"
          :options="permissionOptions"
        />
        <span
          v-else
          class="text-uppercase text-muted font-italic"
          :class="userDataClasses"
          >{{ data.item.permission_type.name }}</span
        >
      </template>
      <template slot="cell(remove)" slot-scope="data">
        <b-link
          v-if="!isPermissionReadOnly(data.item.permission_type)"
          @click="removeUser(data.item.user)"
        >
          <span class="fa fa-trash"></span>
        </b-link>
      </template>
    </b-table>
    <b-table
      v-if="groupsCount > 0"
      id="modal-group-table"
      hover
      :items="sortedGroupPermissions"
      :fields="groupFields"
    >
      <template slot="cell(name)" slot-scope="data">
        <span
          v-if="editingAllowed(data.item.group, data.item.permission_type)"
          >{{ data.item.group.name }}</span
        >
        <span v-else class="text-muted font-italic">{{
          data.item.group.name
        }}</span>
      </template>
      <template slot="cell(permission)" slot-scope="data">
        <b-form-select
          v-if="editingAllowed(data.item.group, data.item.permission_type)"
          v-model="data.item.permission_type"
          :options="permissionOptions"
        />
        <span v-else class="text-muted font-italic">{{
          data.item.permission_type.name
        }}</span>
      </template>
      <template slot="cell(remove)" slot-scope="data">
        <b-link
          v-if="editingAllowed(data.item.group, data.item.permission_type)"
          @click="removeGroup(data.item.group)"
        >
          <span class="fa fa-trash"></span>
        </b-link>
      </template>
    </b-table>
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
