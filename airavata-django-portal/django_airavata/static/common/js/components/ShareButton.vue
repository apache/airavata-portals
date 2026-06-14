<template>
  <div class="inline-block">
    <Button
      variant="outline"
      :title="title"
      :disabled="!shareButtonEnabled"
      @click="openSharingSettingsModal"
    >
      Share
      <Badge variant="secondary">{{ totalCount }}</Badge>
    </Button>
    <Dialog v-model:open="modalOpen" @update:open="onOpenChange">
      <DialogContent
        class="max-h-[90vh] w-[60vw] max-w-[800px] overflow-hidden"
        :show-close-button="false"
        @interact-outside.prevent
        @escape-key-down.prevent
      >
        <DialogHeader>
          <DialogTitle>Sharing Settings</DialogTitle>
        </DialogHeader>
        <div class="max-h-[50vh] min-h-[300px] overflow-auto">
          <shared-entity-editor
            v-if="localSharedEntity && users && groups"
            v-model="localSharedEntity"
            :users="users"
            :groups="groups"
            :disallow-editing-admin-groups="disallowEditingAdminGroups"
          />
          <!-- Only show parent entity permissions for new entities -->
          <template v-if="hasParentSharedEntityPermissions">
            <shared-entity-editor
              v-if="parentSharedEntity && users && groups"
              v-model="parentSharedEntity"
              :users="users"
              :groups="groups"
              :readonly="true"
              class="mt-4"
            >
              <template v-slot:permissions-header>
                <span
                  >Inherited {{ parentEntityLabel }} Permissions
                </span>
              </template>
            </shared-entity-editor>
          </template>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="onCancel">Cancel</Button>
          <Button variant="default" @click="onSave">Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script>
import { models, services } from "django-airavata-api";
import SharedEntityEditor from "./SharedEntityEditor.vue";

export default {
  name: "share-button",
  props: {
    entityId: String,
    parentEntityId: String,
    parentEntityLabel: {
      type: String,
      default: "Parent",
    },
    sharedEntity: models.SharedEntity,
    autoAddDefaultGatewayUsersGroup: {
      type: Boolean,
      default: true,
    },
    autoAddAdminGroups: {
      type: Boolean,
      default: true,
    },
    disallowEditingAdminGroups: {
      type: Boolean,
      default: true,
    },
  },
  components: {
    SharedEntityEditor,
  },
  data: function () {
    return {
      modalOpen: false,
      localSharedEntity: null,
      parentSharedEntity: null,
      sharedEntityCopy: null,
      defaultGatewayUsersGroup: null,
      adminsGroup: null,
      readOnlyAdminsGroup: null,
      users: null,
      groups: null,
    };
  },
  computed: {
    title: function () {
      return (
        "Shared with " +
        this.groupsCount +
        " groups" +
        (this.groupsCount > 0 ? " (" + this.groupNames.join(", ") + ")" : "") +
        " and " +
        this.usersCount +
        " users" +
        (this.usersCount > 0 ? " (" + this.userNames.join(", ") + ")" : "")
      );
    },
    usersCount: function () {
      return this.combinedUsers.length;
    },
    userNames: function () {
      return this.combinedUsers.map((u) => u.first_name + " " + u.last_name);
    },
    combinedUsers() {
      const users = [];
      if (this.localSharedEntity && this.localSharedEntity.user_permissions) {
        users.push(
          ...this.localSharedEntity.user_permissions.map((up) => up.user)
        );
      }
      if (this.parentSharedEntity && this.parentSharedEntity.user_permissions) {
        users.push(
          ...this.parentSharedEntity.user_permissions.map((up) => up.user)
        );
        if (this.parentEntityOwner) {
          users.push(this.parentEntityOwner);
        }
      }
      return users;
    },
    filteredGroupPermissions: function () {
      if (this.localSharedEntity && this.localSharedEntity.group_permissions) {
        return this.localSharedEntity.group_permissions;
      } else {
        return [];
      }
    },
    combinedGroups() {
      const groups = [];
      groups.push(...this.filteredGroupPermissions.map((gp) => gp.group));
      if (this.parentSharedEntity && this.parentSharedEntity.group_permissions) {
        groups.push(
          ...this.parentSharedEntity.group_permissions.map((gp) => gp.group)
        );
      }
      return groups;
    },
    groupNames: function () {
      return this.combinedGroups.map((g) => g.name);
    },
    groupsCount: function () {
      return this.combinedGroups.length;
    },
    totalCount: function () {
      return this.usersCount + this.groupsCount;
    },
    shareButtonEnabled: function () {
      // Enable share button if new entity or user is the entity's owner
      return (
        this.localSharedEntity &&
        (!this.localSharedEntity.entity_id ||
          this.localSharedEntity.is_owner ||
          this.localSharedEntity.has_sharing_permission)
      );
    },
    hasParentSharedEntityPermissions() {
      return (
        this.parentSharedEntity &&
        (this.parentSharedEntity.user_permissions.length > 0 ||
          this.parentSharedEntity.group_permissions.length > 0)
      );
    },
    parentEntityOwner() {
      // Only show the parent entity owner when not the same as current user
      if (this.parentSharedEntity && !this.parentSharedEntity.is_owner) {
        return this.parentSharedEntity.owner;
      } else {
        return null;
      }
    },
  },
  methods: {
    initialize: function () {
      // First loaded needed data and then process it. This is to prevent one
      // call to initialize clobbering a later call to initialize. That is, do
      // all of the async stuff first and then make decisions based on the
      // values of the props.
      const promises = [];
      let loadedSharedEntity = null;
      if (this.entityId) {
        promises.push(
          this.loadSharedEntity(this.entityId).then(
            (sharedEntity) => (loadedSharedEntity = sharedEntity)
          )
        );
      }
      if (
        !this.entityId &&
        (!this.sharedEntity || !this.sharedEntity.entity_id) &&
        (!this.defaultGatewayUsersGroup ||
          !this.adminsGroup ||
          !this.readOnlyAdminsGroup)
      ) {
        promises.push(
          services.GroupService.list({ limit: -1 }).then((groups) => {
            this.groups = groups;
            this.defaultGatewayUsersGroup = groups.find(
              (g) => g.is_default_gateway_users_group
            );
            this.adminsGroup = groups.find((g) => g.is_gateway_admins_group);
            this.readOnlyAdminsGroup = groups.find(
              (g) => g.is_read_only_gateway_admins_group
            );
          })
        );
      }
      if (this.parentEntityId) {
        promises.push(
          this.loadSharedEntity(this.parentEntityId).then(
            (sharedEntity) => (this.parentSharedEntity = sharedEntity)
          )
        );
      }
      Promise.all(promises).then(() => {
        if (this.sharedEntity) {
          this.localSharedEntity = this.sharedEntity.clone();
        } else if (this.entityId) {
          this.localSharedEntity = loadedSharedEntity;
        } else {
          this.localSharedEntity = new models.SharedEntity();
        }
        if (
          !this.localSharedEntity.entity_id &&
          this.autoAddDefaultGatewayUsersGroup &&
          this.defaultGatewayUsersGroup
        ) {
          this.localSharedEntity.addGroup({
            group: this.defaultGatewayUsersGroup,
          });
          this.emitUnsavedEvent();
        }
        if (
          !this.localSharedEntity.entity_id &&
          this.autoAddAdminGroups &&
          this.adminsGroup &&
          this.readOnlyAdminsGroup
        ) {
          this.localSharedEntity.addGroup({
            group: this.adminsGroup,
            permissionType: models.ResourcePermissionType.MANAGE_SHARING,
          });
          this.localSharedEntity.addGroup({ group: this.readOnlyAdminsGroup });
          this.emitUnsavedEvent();
        }
        if (
          this.localSharedEntity.entity_id &&
          this.autoAddAdminGroups &&
          this.localSharedEntity.is_owner
        ) {
          // AIRAVATA-3297 Admins group used to get WRITE permission, but the
          // new default is MANAGE_SHARING so update if necessary
          // Since autoAddAdminGroups is true, there should already be an adminsGroupPermission
          const adminsGroupPermission = this.localSharedEntity.group_permissions.find(
            (gp) => gp.group.is_gateway_admins_group
          );
          if (
            adminsGroupPermission &&
            adminsGroupPermission.permission_type !==
              models.ResourcePermissionType.MANAGE_SHARING
          ) {
            adminsGroupPermission.permission_type =
              models.ResourcePermissionType.MANAGE_SHARING;
            this.emitUnsavedEvent();
          }
        }
      });
    },
    loadSharedEntity(entityId) {
      return services.SharedEntityService.retrieve({ lookup: entityId });
    },
    /**
     * Merge the persisted SharedEntity with the local SharedEntity
     * instance and save it, returning a Promise.
     */
    mergeAndSave: function (entityId) {
      return services.SharedEntityService.merge({
        lookup: entityId,
        data: this.localSharedEntity,
      }).then((sharedEntity) => {
        this.localSharedEntity = sharedEntity;
        this.emitSavedEvent();
      });
    },
    saveSharedEntity: function () {
      // If we don't have an entityId we can't create a SharedEntity. Instead,
      // we'll just emit 'unsaved' to let parent know that sharing has changed.
      // It will be up to parent to call `mergeAndSave(entityId)` once there is
      // an entityId or merge the sharedEntity itself.
      if (this.localSharedEntity.entity_id) {
        services.SharedEntityService.update({
          data: this.localSharedEntity,
          lookup: this.localSharedEntity.entity_id,
        }).then((sharedEntity) => {
          this.localSharedEntity = sharedEntity;
          this.emitSavedEvent();
        });
      } else {
        this.emitUnsavedEvent();
      }
    },
    emitSavedEvent() {
      this.$emit("saved", this.localSharedEntity);
    },
    emitUnsavedEvent() {
      this.$emit("unsaved", this.localSharedEntity);
    },
    cancelEditSharedEntity: function () {
      this.localSharedEntity = this.sharedEntityCopy;
    },
    openSharingSettingsModal: function () {
      this.showSharingSettingsModal();
      this.modalOpen = true;
    },
    showSharingSettingsModal: function () {
      this.sharedEntityCopy = this.localSharedEntity.clone();
      if (!this.users) {
        services.ServiceFactory.service("UserProfiles")
          .list()
          .then((users) => (this.users = users));
      }
      if (!this.groups) {
        services.GroupService.list({ limit: -1 }).then((groups) => {
          this.groups = groups;
        });
      }
    },
    onSave: function () {
      this.saveSharedEntity();
      this.modalOpen = false;
    },
    onCancel: function () {
      this.cancelEditSharedEntity();
      this.modalOpen = false;
    },
    onOpenChange: function (open) {
      // Reka closes the dialog (e.g. via the close affordance) by emitting
      // false; treat that as a cancel so local edits are reverted.
      if (!open) {
        this.cancelEditSharedEntity();
      }
    },
  },
  mounted: function () {
    // Only run initialize when mounted since it may add the default gateways
    // group automatically (autoAddDefaultGatewayUsersGroup)
    this.initialize();
  },
  watch: {
    sharedEntity(newSharedEntity) {
      this.localSharedEntity = newSharedEntity
        ? newSharedEntity.clone()
        : new models.SharedEntity();
    },
    entityId(newEntityId, oldEntityId) {
      if (newEntityId && newEntityId !== oldEntityId) {
        this.loadSharedEntity(newEntityId).then(
          (sharedEntity) => (this.localSharedEntity = sharedEntity)
        );
      }
    },
    parentEntityId(newParentEntityId) {
      this.loadSharedEntity(newParentEntityId).then((sharedEntity) => {
        this.parentSharedEntity = sharedEntity;
      });
    },
  },
};
</script>
