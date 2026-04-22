<template>
  <div class="has-fixed-footer">
    <unsaved-changes-guard :dirty="isDirty" />
    <confirmation-dialog ref="unsavedChangesDialog" title="You have unsaved changes">
      You have unsaved changes. Are you sure you want to leave this page?
    </confirmation-dialog>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">
          {{ title }}
        </h1>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <ul class="nav mb-3" tabs>
          <li class="nav-item">
            <a
              class="nav-link active"
              :to="{
                name: id ? 'application_module' : 'new_application_module',
                params: { id: id },
              }"
              >Details</a
            >
          </li>
          <li class="nav-item">
            <a
              class="nav-link active"
              :to="{ name: 'application_interface', params: { id: id } }"
              :disabled="!id"
              >Interface</a
            >
          </li>
          <li class="nav-item">
            <a
              class="nav-link active"
              :to="{ name: 'application_deployments', params: { id: id } }"
              :disabled="!id"
              >Deployments</a
            >
          </li>
        </ul>
        <router-view
          v-if="appModule"
          v-model="appModule"
          name="module"
          :readonly="!appModule.user_has_write_access"
          :validation-errors="appModuleValidationErrors"
          @input="appModuleIsDirty = true"
        />
        <router-view
          v-if="appInterface"
          v-model="appInterface"
          name="interface"
          :readonly="!appInterface.user_has_write_access"
          @input="appInterfaceIsDirty = true"
        />
        <router-view
          v-if="appModule && appDeployments"
          name="deployments"
          :deployments="appDeployments"
          :readonly="!appModule.user_has_write_access"
          @new="createNewDeployment"
          @delete="deleteApplicationDeployment"
        />
        <router-view
          v-if="currentDeployment && currentDeploymentSharedEntity"
          v-model="currentDeployment"
          name="deployment"
          :shared-entity="currentDeploymentSharedEntity"
          @sharing-changed="deploymentSharingChanged"
          @input="currentDeploymentChanged"
        />
      </div>
    </div>
    <div class="fixed-footer">
      <button
        class="btn btn-primary btn-sm editor-button"
        :disabled="readonly || !isDirty"
        @click="saveAll"
      >
        Save
      </button>
      <delete-button
        v-if="id"
        class="editor-button"
        :disabled="readonly"
        @delete="deleteApplication"
      >
        Are you sure you want to delete the
        <strong>{{ appModule ? appModule.app_module_name : "" }}</strong>
        application?
      </delete-button>
      <button class="btn btn-secondary btn-sm editor-button" @click="cancel">Cancel</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import { errors, models, services, utils as apiUtils } from "django-airavata-api";
import { components, notifications } from "django-airavata-common-ui";

const UnsavedChangesGuard = components.UnsavedChangesGuard;
const ConfirmationDialog = components.ConfirmationDialog;
const DeleteButton = components.DeleteButton;

const props = defineProps<{
  id?: string;
  deploymentId?: string;
  hostId?: string;
}>();

const router = useRouter();
const route = useRoute();

type AppModule = InstanceType<typeof models.ApplicationModule>;
type AppInterface = InstanceType<typeof models.ApplicationInterfaceDefinition>;
type AppDeployment = InstanceType<typeof models.ApplicationDeploymentDescription>;
type SharedEntity = InstanceType<typeof models.SharedEntity>;

const unsavedChangesDialog = ref<InstanceType<typeof ConfirmationDialog> | null>(null);
const appModule = ref<AppModule | null>(null);
const appInterface = ref<AppInterface | null>(null);
const appDeployments = ref<AppDeployment[]>([]);
// Map key is computeHostId, value is SharedEntity
const appDeploymentsSharedEntities = ref<Record<string, SharedEntity>>({});
const currentDeployment = ref<AppDeployment | null>(null);
const currentDeploymentSharedEntity = ref<SharedEntity | null>(null);
const appModuleIsDirty = ref(false);
const appInterfaceIsDirty = ref(false);
const dirtyAppDeploymentComputeHostIds = ref<string[]>([]);
const dirtyAppDeploymentSharedEntityComputeHostIds = ref<string[]>([]);
const appModuleValidationErrors = ref<unknown>(null);

const isDirty = computed(
  () =>
    appModuleIsDirty.value ||
    appInterfaceIsDirty.value ||
    dirtyAppDeploymentComputeHostIds.value.length > 0 ||
    dirtyAppDeploymentSharedEntityComputeHostIds.value.length > 0,
);

const title = computed(() => {
  if (props.id) {
    return appModule.value && (appModule.value as { app_module_name?: string }).app_module_name
      ? (appModule.value as { app_module_name: string }).app_module_name
      : "";
  } else {
    return "Create a New Application";
  }
});

const readonly = computed(
  () => appModule.value && !(appModule.value as { user_has_write_access?: boolean }).user_has_write_access,
);

onBeforeRouteLeave((_to, _from, next) => {
  if (isDirty.value && unsavedChangesDialog.value) {
    const dialog = unsavedChangesDialog.value as unknown as { show(): void; $on(_event: string, _cb: () => void): void };
    dialog.show();
    dialog.$on("ok", next);
  } else {
    next();
  }
});

watch(
  () => route.params,
  (toParams, fromParams) => {
    if (toParams.id !== fromParams.id) {
      initialize();
    }
    initializeDeploymentEditing();
  },
);

onMounted(() => {
  initialize();
});

function initialize() {
  if (props.id) {
    loadApplicationModule(props.id);
    loadApplicationInterface(props.id);
    loadApplicationDeployments(props.id).then(() => {
      initializeDeploymentEditing();
    });
  } else {
    appModule.value = new models.ApplicationModule({
      userHasWriteAccess: true,
    }) as AppModule;
  }
}

function initializeDeploymentEditing() {
  if (props.deploymentId) {
    startEditingExistingDeployment(props.deploymentId);
  } else if (props.hostId) {
    startEditingNewDeployment(props.hostId);
  }
}

function startEditingExistingDeployment(deploymentId: string) {
  setCurrentDeploymentFromAppDeploymentId(deploymentId).then((appDeployment) =>
    setCurrentApplicationDeploymentSharedEntity(appDeployment),
  );
}

function startEditingNewDeployment(computeHostId: string) {
  setCurrentDeploymentFromComputeHostId(computeHostId).then((appDeployment) =>
    setCurrentApplicationDeploymentSharedEntity(appDeployment),
  );
}

function loadApplicationModule(appModuleId: string) {
  return services.ApplicationModuleService.retrieve({
    lookup: appModuleId,
  }).then((mod: unknown) => {
    appModuleIsDirty.value = false;
    appModule.value = mod as AppModule;
  });
}

function createApplicationModule(mod: AppModule) {
  return services.ApplicationModuleService.create({ data: mod }, { ignoreErrors: true });
}

function updateApplicationModule(mod: AppModule) {
  return services.ApplicationModuleService.update(
    {
      lookup: (mod as { app_module_id: string }).app_module_id,
      data: mod,
    },
    { ignoreErrors: true },
  );
}

function saveApplicationModule(mod: AppModule) {
  return (
    props.id ? updateApplicationModule(mod) : createApplicationModule(mod)
  )
    .then((saved: unknown) => {
      appModuleValidationErrors.value = null;
      appModuleIsDirty.value = false;
      appModule.value = saved as AppModule;
      return saved as AppModule;
    })
    .catch((error: unknown) => {
      if (errors.ErrorUtils.isValidationError(error)) {
        appModuleValidationErrors.value = (error as { details: { response: unknown } }).details.response;
      } else {
        appModuleValidationErrors.value = null;
        notifications.NotificationList.addError(error);
      }
      return Promise.reject(error);
    });
}

function deleteApplicationModule() {
  const deleteModule = props.id
    ? services.ApplicationModuleService.delete({ lookup: props.id })
    : Promise.resolve(null);
  return deleteModule.then(() => {
    appModuleIsDirty.value = false;
    appModule.value = null;
  });
}

function loadApplicationInterface(appModuleId: string) {
  return services.ApplicationModuleService.getApplicationInterface(
    { lookup: appModuleId },
    { ignoreErrors: true },
  )
    .then((iface: unknown) => {
      appInterfaceIsDirty.value = false;
      appInterface.value = iface as AppInterface;
      return iface as AppInterface;
    })
    .catch((error: unknown) => {
      if ((error as { details?: { status?: number } }).details?.status === 404) {
        const iface = new models.ApplicationInterfaceDefinition({
          userHasWriteAccess: true,
        }) as AppInterface;
        (iface as { addStandardOutAndStandardErrorOutputs(): void }).addStandardOutAndStandardErrorOutputs();
        appInterface.value = iface;
        appInterfaceIsDirty.value = true;
        return Promise.resolve(null);
      } else {
        throw error;
      }
    })
    .catch(apiUtils.FetchUtils.reportError);
}

function createApplicationInterface(iface: AppInterface) {
  return services.ApplicationInterfaceService.create({
    data: iface,
  }).then((saved: unknown) => {
    appInterfaceIsDirty.value = false;
    appInterface.value = saved as AppInterface;
    return saved as AppInterface;
  });
}

function updateApplicationInterface(iface: AppInterface) {
  return services.ApplicationInterfaceService.update({
    lookup: (iface as { application_interface_id: string }).application_interface_id,
    data: iface,
  }).then((saved: unknown) => {
    appInterfaceIsDirty.value = false;
    appInterface.value = saved as AppInterface;
    return saved as AppInterface;
  });
}

function saveApplicationInterface(iface: AppInterface) {
  (iface as { application_name: string; application_modules: string[] }).application_name =
    (appModule.value as { app_module_name: string }).app_module_name;
  (iface as { application_name: string; application_modules: string[] }).application_modules = [props.id!];
  return (iface as { application_interface_id?: string }).application_interface_id
    ? updateApplicationInterface(iface)
    : createApplicationInterface(iface);
}

function deleteApplicationInterface(iface: AppInterface) {
  if ((iface as { application_interface_id?: string }).application_interface_id) {
    return services.ApplicationInterfaceService.delete({
      lookup: (iface as { application_interface_id: string }).application_interface_id,
    }).then(() => (appInterfaceIsDirty.value = false));
  } else {
    appInterfaceIsDirty.value = false;
    appInterface.value = null;
    return Promise.resolve(null);
  }
}

function loadApplicationDeployments(appModuleId: string) {
  return services.ApplicationModuleService.getApplicationDeployments({
    lookup: appModuleId,
  }).then((deps: unknown) => {
    dirtyAppDeploymentComputeHostIds.value = [];
    appDeployments.value = deps as AppDeployment[];
    return deps as AppDeployment[];
  });
}

function createApplicationDeployment(dep: AppDeployment) {
  return services.ApplicationDeploymentService.create({
    data: dep,
  }).then((saved: unknown) => {
    removeDirtyAppDeploymentComputeHostId(saved as AppDeployment);
    replaceAppDeployment(saved as AppDeployment);
    return saved as AppDeployment;
  });
}

function updateApplicationDeployment(dep: AppDeployment) {
  return services.ApplicationDeploymentService.update({
    lookup: (dep as { app_deployment_id: string }).app_deployment_id,
    data: dep,
  }).then((saved: unknown) => {
    removeDirtyAppDeploymentComputeHostId(saved as AppDeployment);
    replaceAppDeployment(saved as AppDeployment);
    return saved as AppDeployment;
  });
}

function saveApplicationDeployment(dep: AppDeployment) {
  return (dep as { app_deployment_id?: string }).app_deployment_id
    ? updateApplicationDeployment(dep)
    : createApplicationDeployment(dep);
}

function deleteApplicationDeployment(dep: AppDeployment) {
  if ((dep as { app_deployment_id?: string }).app_deployment_id) {
    return services.ApplicationDeploymentService.delete({
      lookup: (dep as { app_deployment_id: string }).app_deployment_id,
    }).then(() => {
      removeDirtyAppDeploymentComputeHostId(dep);
      return loadApplicationDeployments(props.id!);
    });
  } else {
    const depIndex = appDeployments.value.findIndex(
      (d) => (d as { compute_host_id?: string }).compute_host_id === (dep as { compute_host_id?: string }).compute_host_id,
    );
    appDeployments.value.splice(depIndex, 1);
    removeDirtyAppDeploymentComputeHostId(dep);
    return Promise.resolve(appDeployments.value);
  }
}

function currentDeploymentChanged(dep: AppDeployment) {
  replaceAppDeployment(dep);
  setApplicationDeploymentDirty(dep);
}

function replaceAppDeployment(dep: AppDeployment) {
  const depIndex = appDeployments.value.findIndex(
    (d) => (d as { compute_host_id?: string }).compute_host_id === (dep as { compute_host_id?: string }).compute_host_id,
  );
  appDeployments.value.splice(depIndex, 1, dep);
}

function setApplicationDeploymentDirty(dep: AppDeployment) {
  const hostId = (dep as { compute_host_id: string }).compute_host_id;
  if (!dirtyAppDeploymentComputeHostIds.value.includes(hostId)) {
    dirtyAppDeploymentComputeHostIds.value.push(hostId);
  }
}

function removeDirtyAppDeploymentComputeHostId(dep: AppDeployment) {
  const hostId = (dep as { compute_host_id: string }).compute_host_id;
  const hostIdIndex = dirtyAppDeploymentComputeHostIds.value.indexOf(hostId);
  if (hostIdIndex >= 0) {
    dirtyAppDeploymentComputeHostIds.value.splice(hostIdIndex, 1);
  }
}

function createNewDeployment(computeHostId: string) {
  router.push({
    name: "new_application_deployment",
    params: { id: props.id!, hostId: computeHostId },
  });
}

function loadApplicationDeploymentSharedEntity(dep: AppDeployment) {
  return services.SharedEntityService.retrieve({
    lookup: (dep as { app_deployment_id: string }).app_deployment_id,
  }).then((sharedEntity: unknown) => {
    const se = sharedEntity as SharedEntity;
    appDeploymentsSharedEntities.value[(dep as { compute_host_id: string }).compute_host_id] = se;
    removeAppDeploymentSharedEntityDirty(se, dep);
    return se;
  });
}

function setCurrentApplicationDeploymentSharedEntity(dep: AppDeployment) {
  const hostId = (dep as { compute_host_id: string }).compute_host_id;
  if (hostId in appDeploymentsSharedEntities.value) {
    currentDeploymentSharedEntity.value = appDeploymentsSharedEntities.value[hostId];
    return Promise.resolve(currentDeploymentSharedEntity.value);
  } else if ((dep as { app_deployment_id?: string }).app_deployment_id) {
    return loadApplicationDeploymentSharedEntity(dep).then(
      (se: SharedEntity) => (currentDeploymentSharedEntity.value = se),
    );
  } else {
    throw new Error("Could not find shared entity in local map and cannot fetch");
  }
}

function deploymentSharingChanged(deploymentSharedEntity: SharedEntity, dep: AppDeployment, dirty: boolean) {
  currentDeploymentSharedEntity.value = deploymentSharedEntity;
  replaceAppDeploymentSharedEntity(deploymentSharedEntity, dep);
  if (dirty) {
    setApplicationDeploymentSharedEntityDirty(deploymentSharedEntity, dep);
  } else {
    removeAppDeploymentSharedEntityDirty(deploymentSharedEntity, dep);
  }
}

function mergeSharedEntity(sharedEntity: SharedEntity, dep: AppDeployment) {
  return services.SharedEntityService.merge({
    data: sharedEntity,
    lookup: (dep as { app_deployment_id: string }).app_deployment_id,
  }).then((se: unknown) => {
    replaceAppDeploymentSharedEntity(se as SharedEntity, dep);
    removeAppDeploymentSharedEntityDirty(se as SharedEntity, dep);
    return se as SharedEntity;
  });
}

function updateSharedEntity(sharedEntity: SharedEntity, dep: AppDeployment) {
  return services.SharedEntityService.update({
    data: sharedEntity,
    lookup: (dep as { app_deployment_id: string }).app_deployment_id,
  }).then((se: unknown) => {
    replaceAppDeploymentSharedEntity(se as SharedEntity, dep);
    removeAppDeploymentSharedEntityDirty(se as SharedEntity, dep);
    return se as SharedEntity;
  });
}

function saveSharedEntity(sharedEntity: SharedEntity, dep: AppDeployment) {
  return (sharedEntity as { entity_id?: string }).entity_id
    ? updateSharedEntity(sharedEntity, dep)
    : mergeSharedEntity(sharedEntity, dep);
}

function setApplicationDeploymentSharedEntityDirty(_sharedEntity: SharedEntity, dep: AppDeployment) {
  const hostId = (dep as { compute_host_id: string }).compute_host_id;
  if (!dirtyAppDeploymentSharedEntityComputeHostIds.value.includes(hostId)) {
    dirtyAppDeploymentSharedEntityComputeHostIds.value.push(hostId);
  }
}

function removeAppDeploymentSharedEntityDirty(_sharedEntity: SharedEntity, dep: AppDeployment) {
  const hostId = (dep as { compute_host_id: string }).compute_host_id;
  const hostIdIndex = dirtyAppDeploymentSharedEntityComputeHostIds.value.indexOf(hostId);
  if (hostIdIndex >= 0) {
    dirtyAppDeploymentSharedEntityComputeHostIds.value.splice(hostIdIndex, 1);
  }
}

function replaceAppDeploymentSharedEntity(sharedEntity: SharedEntity, dep: AppDeployment) {
  appDeploymentsSharedEntities.value[(dep as { compute_host_id: string }).compute_host_id] = sharedEntity;
}

function setCurrentDeploymentFromAppDeploymentId(appDeploymentId: string) {
  currentDeployment.value = appDeployments.value.find(
    (dep) => (dep as { app_deployment_id?: string }).app_deployment_id === appDeploymentId,
  ) ?? null;
  if (!currentDeployment.value) {
    throw new Error("Unable to find deployment from appDeploymentId=" + appDeploymentId);
  }
  return Promise.resolve(currentDeployment.value);
}

function setCurrentDeploymentFromComputeHostId(computeHostId: string) {
  currentDeployment.value = appDeployments.value.find(
    (dep) => (dep as { compute_host_id?: string }).compute_host_id === computeHostId,
  ) ?? null;
  if (!currentDeployment.value) {
    const deployment = new models.ApplicationDeploymentDescription({
      userHasWriteAccess: true,
    }) as AppDeployment;
    (deployment as { app_module_id: string }).app_module_id = props.id!;
    (deployment as { compute_host_id: string }).compute_host_id = computeHostId;
    currentDeployment.value = deployment;
    appDeployments.value.push(deployment);
    setApplicationDeploymentDirty(deployment);
    appDeploymentsSharedEntities.value[computeHostId] = new models.SharedEntity() as SharedEntity;
  }
  return Promise.resolve(currentDeployment.value);
}

function saveAll() {
  const moduleSave = appModuleIsDirty.value
    ? saveApplicationModule(appModule.value!).catch((error: unknown) => {
        router.push({
          name: props.id ? "application_module" : "new_application_module",
        });
        return Promise.reject(error);
      })
    : Promise.resolve(appModule.value);
  const interfaceSave = moduleSave.then(() =>
    appInterfaceIsDirty.value
      ? saveApplicationInterface(appInterface.value!).catch((error: unknown) => {
          router.push({ name: "application_interface" });
          return Promise.reject(error);
        })
      : Promise.resolve(appInterface.value),
  );
  interfaceSave
    .then(() => {
      return Promise.all(
        dirtyAppDeploymentComputeHostIds.value.map((computeHostId) => {
          const deployment = appDeployments.value.find(
            (dep) => (dep as { compute_host_id?: string }).compute_host_id === computeHostId,
          )!;
          return saveApplicationDeployment(deployment).catch((error: unknown) => {
            if ((deployment as { app_deployment_id?: string }).app_deployment_id) {
              router.push({
                name: "application_deployment",
                params: {
                  id: props.id!,
                  deploymentId: (deployment as { app_deployment_id: string }).app_deployment_id,
                },
              });
            } else {
              router.push({
                name: "new_application_deployment",
                params: { id: props.id!, hostId: (deployment as { compute_host_id: string }).compute_host_id },
              });
            }
            return Promise.reject(error);
          });
        }),
      );
    })
    .then(() => {
      return Promise.all(
        dirtyAppDeploymentSharedEntityComputeHostIds.value.map((computeHostId) => {
          const sharedEntity = appDeploymentsSharedEntities.value[computeHostId];
          const deployment = appDeployments.value.find(
            (dep) => (dep as { compute_host_id?: string }).compute_host_id === computeHostId,
          )!;
          return saveSharedEntity(sharedEntity, deployment).catch((error: unknown) => {
            if ((deployment as { app_deployment_id?: string }).app_deployment_id) {
              router.push({
                name: "application_deployment",
                params: {
                  id: props.id!,
                  deploymentId: (deployment as { app_deployment_id: string }).app_deployment_id,
                },
              });
            } else {
              router.push({
                name: "new_application_deployment",
                params: {
                  id: props.id!,
                  hostId: (deployment as { compute_host_id: string }).compute_host_id,
                },
              });
            }
            return Promise.reject(error);
          });
        }),
      );
    })
    .then(() => {
      notifications.NotificationList.add(
        new notifications.Notification({
          type: "SUCCESS",
          message: "Application saved successfully",
          duration: 5,
        }),
      );
      if (!props.id && (appModule.value as { app_module_id?: string })?.app_module_id) {
        router.push({
          name: "application_module",
          params: { id: (appModule.value as { app_module_id: string }).app_module_id },
        });
      }
      if (props.hostId) {
        router.push({
          name: "application_deployments",
          params: { id: (appModule.value as { app_module_id: string }).app_module_id },
        });
      } else {
        initializeDeploymentEditing();
      }
    });
}

function cancel() {
  router.push({ path: "/applications" });
}

function deleteApplication() {
  const deleteAllDeployments = appDeployments.value.map((dep) => deleteApplicationDeployment(dep));
  return Promise.all(deleteAllDeployments)
    .then(() => deleteApplicationInterface(appInterface.value!))
    .then(() => deleteApplicationModule())
    .then(() => {
      router.push({ path: "/applications" });
    });
}
</script>

<style scoped>
/* style the containing div, in base.html template */
/* .main-content {
    background-color: #ffffff;
} */
.editor-button + .editor-button {
  margin-left: 0.25em;
}
</style>
