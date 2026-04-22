<template>
  <div class="share-button">
    <button
      type="button"
      class="btn btn-outline-secondary btn-pill"
      :disabled="!shareButtonEnabled"
      :title="title"
      @click="handleShareClick"
    >
      <i class="fa fa-share-alt me-1" aria-hidden="true"></i>Share
      <span v-if="totalCount > 0" class="badge bg-secondary ms-1">{{ totalCount }}</span>
    </button>
    <!-- Bootstrap 5 modal -->
    <div
      ref="sharingSettingsModal"
      class="modal fade modal-share-settings"
      tabindex="-1"
      aria-labelledby="sharingSttingsModalLabel"
      aria-hidden="true"
      data-bs-backdrop="static"
      data-bs-keyboard="false"
    >
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 id="sharingSettingsModalLabel" class="modal-title">Sharing Settings</h5>
          </div>
          <div class="modal-body">
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
                <template #permissions-header>
                  <span>Inherited {{ parentEntityLabel }} Permissions</span>
                </template>
              </shared-entity-editor>
            </template>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="cancelEditSharedEntity">
              Cancel
            </button>
            <button type="button" class="btn btn-primary" @click="saveSharedEntity">Save</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models, services } from "django-airavata-api";
import { Modal } from "bootstrap";
import SharedEntityEditor from "./SharedEntityEditor.vue";

const props = withDefaults(defineProps<{
  entityId?: string;
  parentEntityId?: string;
  parentEntityLabel?: string;
  sharedEntity?: InstanceType<typeof models.SharedEntity> | null;
  autoAddDefaultGatewayUsersGroup?: boolean;
  autoAddAdminGroups?: boolean;
  disallowEditingAdminGroups?: boolean;
}>(), {
  entityId: undefined,
  parentEntityId: undefined,
  parentEntityLabel: "Parent",
  sharedEntity: null,
  autoAddDefaultGatewayUsersGroup: true,
  autoAddAdminGroups: true,
  disallowEditingAdminGroups: true,
});

const emit = defineEmits<{
  saved: [sharedEntity: InstanceType<typeof models.SharedEntity>];
  unsaved: [sharedEntity: InstanceType<typeof models.SharedEntity>];
}>();

const sharingSettingsModal = ref<HTMLElement | null>(null);
const localSharedEntity = ref<InstanceType<typeof models.SharedEntity> | null>(null);
const parentSharedEntity = ref<InstanceType<typeof models.SharedEntity> | null>(null);
const sharedEntityCopy = ref<InstanceType<typeof models.SharedEntity> | null>(null);
const defaultGatewayUsersGroup = ref<unknown>(null);
const adminsGroup = ref<unknown>(null);
const readOnlyAdminsGroup = ref<unknown>(null);
const users = ref<unknown[] | null>(null);
const groups = ref<unknown[] | null>(null);
let bsModal: Modal | null = null;

const combinedUsers = computed(() => {
  const userList: unknown[] = [];
  if (localSharedEntity.value && localSharedEntity.value.user_permissions) {
    userList.push(...localSharedEntity.value.user_permissions.map((up: { user: unknown }) => up.user));
  }
  if (parentSharedEntity.value && parentSharedEntity.value.user_permissions) {
    userList.push(...parentSharedEntity.value.user_permissions.map((up: { user: unknown }) => up.user));
    if (parentEntityOwner.value) {
      userList.push(parentEntityOwner.value);
    }
  }
  return userList;
});

const usersCount = computed(() => combinedUsers.value.length);
const userNames = computed(() =>
  combinedUsers.value.map((u) => {
    const user = u as { first_name?: string; last_name?: string };
    return `${user.first_name} ${user.last_name}`;
  }),
);

const filteredGroupPermissions = computed(() => {
  if (localSharedEntity.value && localSharedEntity.value.group_permissions) {
    return localSharedEntity.value.group_permissions;
  } else {
    return [];
  }
});

const combinedGroups = computed(() => {
  const groupList: unknown[] = [];
  groupList.push(...filteredGroupPermissions.value.map((gp: { group: unknown }) => gp.group));
  if (parentSharedEntity.value && parentSharedEntity.value.group_permissions) {
    groupList.push(...parentSharedEntity.value.group_permissions.map((gp: { group: unknown }) => gp.group));
  }
  return groupList;
});

const groupNames = computed(() =>
  combinedGroups.value.map((g) => (g as { name?: string }).name),
);
const groupsCount = computed(() => combinedGroups.value.length);
const totalCount = computed(() => usersCount.value + groupsCount.value);

const title = computed(
  () =>
    "Shared with " +
    groupsCount.value +
    " groups" +
    (groupsCount.value > 0 ? " (" + groupNames.value.join(", ") + ")" : "") +
    " and " +
    usersCount.value +
    " users" +
    (usersCount.value > 0 ? " (" + userNames.value.join(", ") + ")" : ""),
);

const shareButtonEnabled = computed(() => {
  // Enable share button if new entity or user is the entity's owner
  return (
    localSharedEntity.value &&
    (!localSharedEntity.value.entity_id ||
      localSharedEntity.value.is_owner ||
      localSharedEntity.value.has_sharing_permission)
  );
});

const hasParentSharedEntityPermissions = computed(() => {
  return (
    parentSharedEntity.value &&
    (parentSharedEntity.value.user_permissions.length > 0 ||
      parentSharedEntity.value.group_permissions.length > 0)
  );
});

const parentEntityOwner = computed(() => {
  // Only show the parent entity owner when not the same as current user
  if (parentSharedEntity.value && !parentSharedEntity.value.is_owner) {
    return parentSharedEntity.value.owner;
  } else {
    return null;
  }
});

watch(
  () => props.sharedEntity,
  (newSharedEntity) => {
    localSharedEntity.value = newSharedEntity ? newSharedEntity.clone() : new models.SharedEntity();
  },
);

watch(
  () => props.entityId,
  (newEntityId, oldEntityId) => {
    if (newEntityId && newEntityId !== oldEntityId) {
      loadSharedEntity(newEntityId).then((se) => (localSharedEntity.value = se));
    }
  },
);

watch(
  () => props.parentEntityId,
  (newParentEntityId) => {
    if (newParentEntityId) {
      loadSharedEntity(newParentEntityId).then((se) => {
        parentSharedEntity.value = se;
      });
    }
  },
);

onMounted(() => {
  // Only run initialize when mounted since it may add the default gateways
  // group automatically (autoAddDefaultGatewayUsersGroup)
  initialize();
});

function initialize(): void {
  // First loaded needed data and then process it. This is to prevent one
  // call to initialize clobbering a later call to initialize. That is, do
  // all of the async stuff first and then make decisions based on the
  // values of the props.
  const promises: Promise<void>[] = [];
  let loadedSharedEntity: InstanceType<typeof models.SharedEntity> | null = null;
  if (props.entityId) {
    promises.push(
      loadSharedEntity(props.entityId).then((se) => {
        loadedSharedEntity = se;
      }),
    );
  }
  // Group-based sharing has been deprecated; sharing is now user-level only.
  if (!groups.value) {
    groups.value = [];
  }
  if (props.parentEntityId) {
    promises.push(
      loadSharedEntity(props.parentEntityId).then((se) => {
        parentSharedEntity.value = se;
      }),
    );
  }
  Promise.all(promises).then(() => {
    if (props.sharedEntity) {
      localSharedEntity.value = props.sharedEntity.clone();
    } else if (props.entityId) {
      localSharedEntity.value = loadedSharedEntity;
    } else {
      localSharedEntity.value = new models.SharedEntity();
    }
    if (
      localSharedEntity.value &&
      !localSharedEntity.value.entity_id &&
      props.autoAddDefaultGatewayUsersGroup &&
      defaultGatewayUsersGroup.value
    ) {
      localSharedEntity.value.addGroup({
        group: defaultGatewayUsersGroup.value,
      });
      emitUnsavedEvent();
    }
    if (
      localSharedEntity.value &&
      !localSharedEntity.value.entity_id &&
      props.autoAddAdminGroups &&
      adminsGroup.value &&
      readOnlyAdminsGroup.value
    ) {
      localSharedEntity.value.addGroup({
        group: adminsGroup.value,
        permissionType: models.ResourcePermissionType.MANAGE_SHARING,
      });
      localSharedEntity.value.addGroup({ group: readOnlyAdminsGroup.value });
      emitUnsavedEvent();
    }
    if (
      localSharedEntity.value &&
      localSharedEntity.value.entity_id &&
      props.autoAddAdminGroups &&
      localSharedEntity.value.is_owner
    ) {
      // AIRAVATA-3297 Admins group used to get WRITE permission, but the
      // new default is MANAGE_SHARING so update if necessary
      // Since autoAddAdminGroups is true, there should already be an adminsGroupPermission
      const adminsGroupPermission = localSharedEntity.value.group_permissions.find(
        (gp: { group: { is_gateway_admins_group?: boolean } }) => gp.group.is_gateway_admins_group,
      );
      if (
        adminsGroupPermission &&
        adminsGroupPermission.permission_type !== models.ResourcePermissionType.MANAGE_SHARING
      ) {
        adminsGroupPermission.permission_type = models.ResourcePermissionType.MANAGE_SHARING;
        emitUnsavedEvent();
      }
    }
  });
}

function loadSharedEntity(entityId: string): Promise<InstanceType<typeof models.SharedEntity>> {
  return services.SharedEntityService.retrieve({ lookup: entityId });
}

/**
 * Merge the persisted SharedEntity with the local SharedEntity
 * instance and save it, returning a Promise.
 */
function mergeAndSave(entityId: string): Promise<void> {
  return services.SharedEntityService.merge({
    lookup: entityId,
    data: localSharedEntity.value,
  }).then((se: InstanceType<typeof models.SharedEntity>) => {
    localSharedEntity.value = se;
    emitSavedEvent();
  });
}

function saveSharedEntity(): void {
  // If we don't have an entityId we can't create a SharedEntity. Instead,
  // we'll just emit 'unsaved' to let parent know that sharing has changed.
  // It will be up to parent to call `mergeAndSave(entityId)` once there is
  // an entityId or merge the sharedEntity itself.
  if (localSharedEntity.value?.entity_id) {
    services.SharedEntityService.update({
      data: localSharedEntity.value,
      lookup: localSharedEntity.value.entity_id,
    }).then((se: InstanceType<typeof models.SharedEntity>) => {
      localSharedEntity.value = se;
      emitSavedEvent();
      closeModal();
    });
  } else {
    emitUnsavedEvent();
    closeModal();
  }
}

function emitSavedEvent(): void {
  if (localSharedEntity.value) {
    emit("saved", localSharedEntity.value);
  }
}

function emitUnsavedEvent(): void {
  if (localSharedEntity.value) {
    emit("unsaved", localSharedEntity.value);
  }
}

function cancelEditSharedEntity(): void {
  localSharedEntity.value = sharedEntityCopy.value;
  closeModal();
}

function handleShareClick(): void {
  if (!shareButtonEnabled.value) {
    return;
  }
  openSharingSettingsModal();
}

function openSharingSettingsModal(): void {
  if (!localSharedEntity.value) {
    return;
  }
  sharedEntityCopy.value = localSharedEntity.value.clone();
  if (!users.value) {
    services.ServiceFactory.service("UserProfiles")
      .list()
      .then((u: unknown[]) => (users.value = u));
  }
  if (!groups.value) {
    // Group-based sharing is deprecated; user-level sharing only.
    groups.value = [];
  }
  if (!bsModal && sharingSettingsModal.value) {
    bsModal = new Modal(sharingSettingsModal.value);
  }
  bsModal?.show();
}

function closeModal(): void {
  bsModal?.hide();
}

defineExpose({ mergeAndSave });
</script>

<style scoped>
.share-button {
  display: inline-block;
}
.share-button > button {
  white-space: nowrap;
}
.share-button :deep(.modal-share-settings .modal-body) {
  max-height: 50vh;
  min-height: 300px;
  overflow: auto;
}
.share-button :deep(.modal-dialog) {
  max-width: 800px;
  width: 60vw;
}
</style>
