<template>
  <main-layout
    :title="title"
    subtitle="Configure this application's details, interface, and deployments."
  >
    <unsaved-changes-guard :dirty="isDirty" />
    <confirmation-dialog
      ref="unsavedChangesDialog"
      title="You have unsaved changes"
      @ok="onUnsavedChangesConfirmed"
    >
      You have unsaved changes. Are you sure you want to leave this page?
    </confirmation-dialog>
    <div class="pb-20">
      <nav class="mb-3 flex gap-1 border-b">
        <router-link
          class="border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
          exact-active-class="!border-primary !text-foreground"
          :to="{
            name: id ? 'application_module' : 'new_application_module',
            params: { id: id },
          }"
          >Details</router-link
        >
        <router-link
          v-if="id"
          class="border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
          exact-active-class="!border-primary !text-foreground"
          :to="{ name: 'application_interface', params: { id: id } }"
          >Interface</router-link
        >
        <span
          v-else
          class="cursor-not-allowed border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground opacity-50"
          >Interface</span
        >
        <router-link
          v-if="id"
          class="border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
          active-class="!border-primary !text-foreground"
          :to="{ name: 'application_deployments', params: { id: id } }"
          >Deployments</router-link
        >
        <span
          v-else
          class="cursor-not-allowed border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground opacity-50"
          >Deployments</span
        >
      </nav>
      <router-view
        name="module"
        v-if="appModule"
        v-model="appModule"
        @input="appModuleIsDirty = true"
        :readonly="!appModule.user_has_write_access"
        :validation-errors="appModuleValidationErrors"
      />
      <router-view
        name="interface"
        v-if="appInterface"
        v-model="appInterface"
        @input="appInterfaceIsDirty = true"
        :readonly="!appInterface.user_has_write_access"
      />
      <router-view
        name="deployments"
        v-if="appModule && appDeployments"
        :deployments="appDeployments"
        @new="createNewDeployment"
        @delete="deleteApplicationDeployment"
        :readonly="!appModule.user_has_write_access"
      />
      <router-view
        name="deployment"
        v-if="currentDeployment && currentDeploymentSharedEntity"
        v-model="currentDeployment"
        :shared-entity="currentDeploymentSharedEntity"
        @sharing-changed="deploymentSharingChanged"
        @input="currentDeploymentChanged"
      />
    </div>
    <div
      class="bg-background fixed inset-x-0 bottom-0 flex gap-2 border-t p-4 shadow-md"
    >
      <Button
        variant="default"
        @click="saveAll"
        :disabled="readonly || !isDirty"
      >
        Save
      </Button>
      <delete-button v-if="id" :disabled="readonly" @delete="deleteApplication">
        Are you sure you want to delete the
        <strong>{{ appModule ? appModule.app_module_name : "" }}</strong>
        application?
      </delete-button>
      <Button variant="secondary" @click="cancel"> Cancel </Button>
    </div>
  </main-layout>
</template>

<script>
import {
  errors,
  models,
  services,
  utils as apiUtils,
} from "django-airavata-api";
import { components, notifications } from "django-airavata-common-ui";

export default {
  name: "application-editor-container",
  props: {
    id: String,
    deploymentId: String,
    hostId: String,
  },
  components: {
    "main-layout": components.MainLayout,
    "unsaved-changes-guard": components.UnsavedChangesGuard,
    "confirmation-dialog": components.ConfirmationDialog,
    "delete-button": components.DeleteButton,
  },
  data: function () {
    return {
      appModule: null,
      appInterface: null,
      appDeployments: [],
      // Map key is computeHostId, value is SharedEntity
      appDeploymentsSharedEntities: {},
      currentDeployment: null,
      currentDeploymentSharedEntity: null,
      appModuleIsDirty: false,
      appInterfaceIsDirty: false,
      dirtyAppDeploymentComputeHostIds: [],
      dirtyAppDeploymentSharedEntityComputeHostIds: [],
      appModuleValidationErrors: null,
      // Pending vue-router navigation continuation, resolved when the unsaved
      // changes dialog is confirmed (replaces the removed instance $on("ok")).
      pendingNavigation: null,
    };
  },
  computed: {
    title: function () {
      if (this.id) {
        return this.appModule && this.appModule.app_module_name
          ? this.appModule.app_module_name
          : "Application";
      } else {
        return "Create a New Application";
      }
    },
    isDirty() {
      return (
        this.appModuleIsDirty ||
        this.appInterfaceIsDirty ||
        this.dirtyAppDeploymentComputeHostIds.length > 0 ||
        this.dirtyAppDeploymentSharedEntityComputeHostIds.length > 0
      );
    },
    readonly() {
      return this.appModule && !this.appModule.user_has_write_access;
    },
  },
  created() {
    this.initialize();
  },
  methods: {
    initialize() {
      if (this.id) {
        this.loadApplicationModule(this.id);
        this.loadApplicationInterface(this.id);
        this.loadApplicationDeployments(this.id).then(() => {
          this.initializeDeploymentEditing();
        });
      } else {
        this.appModule = new models.ApplicationModule({
          user_has_write_access: true,
        });
      }
    },
    initializeDeploymentEditing() {
      if (this.deploymentId) {
        this.startEditingExistingDeployment(this.deploymentId);
      } else if (this.hostId) {
        this.startEditingNewDeployment(this.hostId);
      }
    },
    startEditingExistingDeployment(deploymentId) {
      this.setCurrentDeploymentFromAppDeploymentId(deploymentId).then(
        (appDeployment) =>
          this.setCurrentApplicationDeploymentSharedEntity(appDeployment),
      );
    },
    startEditingNewDeployment(computeHostId) {
      this.setCurrentDeploymentFromComputeHostId(computeHostId).then(
        (appDeployment) =>
          this.setCurrentApplicationDeploymentSharedEntity(appDeployment),
      );
    },
    loadApplicationModule(appModuleId) {
      return services.ApplicationModuleService.retrieve({
        lookup: appModuleId,
      }).then((appModule) => {
        this.appModuleIsDirty = false;
        this.appModule = appModule;
      });
    },
    createApplicationModule(appModule) {
      return services.ApplicationModuleService.create(
        { data: appModule },
        { ignoreErrors: true },
      );
    },
    updateApplicationModule(appModule) {
      return services.ApplicationModuleService.update(
        {
          lookup: appModule.app_module_id,
          data: appModule,
        },
        { ignoreErrors: true },
      );
    },
    saveApplicationModule(appModule) {
      return (
        this.id
          ? this.updateApplicationModule(appModule)
          : this.createApplicationModule(appModule)
      )
        .then((appModule) => {
          this.appModuleValidationErrors = null;
          this.appModuleIsDirty = false;
          this.appModule = appModule;
          return appModule;
        })
        .catch((error) => {
          if (errors.ErrorUtils.isValidationError(error)) {
            this.appModuleValidationErrors = error.details.response;
          } else {
            this.appModuleValidationErrors = null;
            notifications.NotificationList.addError(error);
          }
          return Promise.reject(error);
        });
    },
    deleteApplicationModule() {
      const deleteModule = this.id
        ? services.ApplicationModuleService.delete({
            lookup: this.id,
          })
        : Promise.resolve(null);
      return deleteModule.then(() => {
        this.appModuleIsDirty = false;
        this.appModule = null;
      });
    },
    loadApplicationInterface(appModuleId) {
      return services.ApplicationModuleService.getApplicationInterface(
        { lookup: appModuleId },
        { ignoreErrors: true },
      )
        .then((appInterface) => {
          this.appInterfaceIsDirty = false;
          this.appInterface = appInterface;
          return appInterface;
        })
        .catch((error) => {
          if (error.details.status === 404) {
            // If there is no interface, just create a new instance
            const appInterface = new models.ApplicationInterfaceDefinition({
              user_has_write_access: true,
            });
            appInterface.addStandardOutAndStandardErrorOutputs();
            this.appInterface = appInterface;
            this.appInterfaceIsDirty = true;
            return Promise.resolve(null);
          } else {
            throw error;
          }
        })
        .catch(apiUtils.FetchUtils.reportError);
    },
    createApplicationInterface(appInterface) {
      return services.ApplicationInterfaceService.create({
        data: appInterface,
      }).then((appInterface) => {
        this.appInterfaceIsDirty = false;
        this.appInterface = appInterface;
        return appInterface;
      });
    },
    updateApplicationInterface(appInterface) {
      return services.ApplicationInterfaceService.update({
        lookup: appInterface.application_interface_id,
        data: appInterface,
      }).then((appInterface) => {
        this.appInterfaceIsDirty = false;
        this.appInterface = appInterface;
        return appInterface;
      });
    },
    saveApplicationInterface(appInterface) {
      appInterface.application_name = this.appModule.app_module_name;
      appInterface.application_modules = [this.id];
      return appInterface.application_interface_id
        ? this.updateApplicationInterface(appInterface)
        : this.createApplicationInterface(appInterface);
    },
    deleteApplicationInterface(appInterface) {
      if (appInterface.application_interface_id) {
        return services.ApplicationInterfaceService.delete({
          lookup: appInterface.application_interface_id,
        }).then(() => (this.appInterfaceIsDirty = false));
      } else {
        this.appInterfaceIsDirty = false;
        this.appInterface = null;
        return Promise.resolve(null);
      }
    },
    loadApplicationDeployments(appModuleId) {
      return services.ApplicationModuleService.getApplicationDeployments({
        lookup: appModuleId,
      }).then((appDeployments) => {
        this.dirtyAppDeploymentComputeHostIds = [];
        this.appDeployments = appDeployments;
        return appDeployments;
      });
    },
    loadApplicationDeployment(appDeploymentId) {
      return services.ApplicationDeploymentService.retrieve({
        lookup: appDeploymentId,
      }).then((appDeployment) => {
        this.currentDeployment = appDeployment;
        return appDeployment;
      });
    },
    createApplicationDeployment(appDeployment) {
      return services.ApplicationDeploymentService.create({
        data: appDeployment,
      }).then((appDeployment) => {
        this.removeDirtyAppDeploymentComputeHostId(appDeployment);
        this.replaceAppDeployment(appDeployment);
        return appDeployment;
      });
    },
    updateApplicationDeployment(appDeployment) {
      return services.ApplicationDeploymentService.update({
        lookup: appDeployment.app_deployment_id,
        data: appDeployment,
      }).then((appDeployment) => {
        this.removeDirtyAppDeploymentComputeHostId(appDeployment);
        this.replaceAppDeployment(appDeployment);
        return appDeployment;
      });
    },
    saveApplicationDeployment(appDeployment) {
      return appDeployment.app_deployment_id
        ? this.updateApplicationDeployment(appDeployment)
        : this.createApplicationDeployment(appDeployment);
    },
    deleteApplicationDeployment(appDeployment) {
      if (appDeployment.app_deployment_id) {
        return services.ApplicationDeploymentService.delete({
          lookup: appDeployment.app_deployment_id,
        }).then(() => {
          this.removeDirtyAppDeploymentComputeHostId(appDeployment);
          return this.loadApplicationDeployments(this.id);
        });
      } else {
        const depIndex = this.appDeployments.findIndex(
          (dep) => dep.compute_host_id === appDeployment.compute_host_id,
        );
        this.appDeployments.splice(depIndex, 1);
        this.removeDirtyAppDeploymentComputeHostId(appDeployment);
        return Promise.resolve(this.appDeployments);
      }
    },
    currentDeploymentChanged(appDeployment) {
      this.replaceAppDeployment(appDeployment);
      this.setApplicationDeploymentDirty(appDeployment);
    },
    replaceAppDeployment(appDeployment) {
      const depIndex = this.appDeployments.findIndex(
        (dep) => dep.compute_host_id === appDeployment.compute_host_id,
      );
      this.appDeployments.splice(depIndex, 1, appDeployment);
    },
    setApplicationDeploymentDirty(appDeployment) {
      if (
        !this.dirtyAppDeploymentComputeHostIds.includes(
          appDeployment.compute_host_id,
        )
      ) {
        this.dirtyAppDeploymentComputeHostIds.push(
          appDeployment.compute_host_id,
        );
      }
    },
    removeDirtyAppDeploymentComputeHostId(appDeployment) {
      const hostIdIndex = this.dirtyAppDeploymentComputeHostIds.indexOf(
        appDeployment.compute_host_id,
      );
      if (hostIdIndex >= 0) {
        this.dirtyAppDeploymentComputeHostIds.splice(hostIdIndex, 1);
      }
    },
    createNewDeployment(computeHostId) {
      this.$router.push({
        name: "new_application_deployment",
        params: { id: this.id, hostId: computeHostId },
      });
    },
    loadApplicationDeploymentSharedEntity(appDeployment) {
      return services.SharedEntityService.retrieve({
        lookup: appDeployment.app_deployment_id,
      }).then((sharedEntity) => {
        this.appDeploymentsSharedEntities[appDeployment.compute_host_id] =
          sharedEntity;
        this.removeAppDeploymentSharedEntityDirty(sharedEntity, appDeployment);
        return sharedEntity;
      });
    },
    setCurrentApplicationDeploymentSharedEntity(appDeployment) {
      if (appDeployment.compute_host_id in this.appDeploymentsSharedEntities) {
        this.currentDeploymentSharedEntity =
          this.appDeploymentsSharedEntities[appDeployment.compute_host_id];
        return Promise.resolve(this.currentDeploymentSharedEntity);
      } else if (appDeployment.app_deployment_id) {
        return this.loadApplicationDeploymentSharedEntity(appDeployment).then(
          (sharedEntity) => (this.currentDeploymentSharedEntity = sharedEntity),
        );
      } else {
        throw new Error(
          "Could not find shared entity in local map and cannot fetch",
        );
      }
    },
    deploymentSharingChanged(deploymentSharedEntity, appDeployment, dirty) {
      this.currentDeploymentSharedEntity = deploymentSharedEntity;
      this.replaceAppDeploymentSharedEntity(
        deploymentSharedEntity,
        appDeployment,
      );
      if (dirty) {
        this.setApplicationDeploymentSharedEntityDirty(
          deploymentSharedEntity,
          appDeployment,
        );
      } else {
        this.removeAppDeploymentSharedEntityDirty(
          deploymentSharedEntity,
          appDeployment,
        );
      }
    },
    mergeSharedEntity(sharedEntity, appDeployment) {
      return services.SharedEntityService.merge({
        data: sharedEntity,
        lookup: appDeployment.app_deployment_id,
      }).then((sharedEntity) => {
        this.replaceAppDeploymentSharedEntity(sharedEntity, appDeployment);
        this.removeAppDeploymentSharedEntityDirty(sharedEntity, appDeployment);
        return sharedEntity;
      });
    },
    updateSharedEntity(sharedEntity, appDeployment) {
      return services.SharedEntityService.update({
        data: sharedEntity,
        lookup: appDeployment.app_deployment_id,
      }).then((sharedEntity) => {
        this.replaceAppDeploymentSharedEntity(sharedEntity, appDeployment);
        this.removeAppDeploymentSharedEntityDirty(sharedEntity, appDeployment);
        return sharedEntity;
      });
    },
    saveSharedEntity(sharedEntity, appDeployment) {
      return sharedEntity.entity_id
        ? this.updateSharedEntity(sharedEntity, appDeployment)
        : this.mergeSharedEntity(sharedEntity, appDeployment);
    },
    setApplicationDeploymentSharedEntityDirty(sharedEntity, appDeployment) {
      if (
        !this.dirtyAppDeploymentSharedEntityComputeHostIds.includes(
          appDeployment.compute_host_id,
        )
      ) {
        this.dirtyAppDeploymentSharedEntityComputeHostIds.push(
          appDeployment.compute_host_id,
        );
      }
    },
    removeAppDeploymentSharedEntityDirty(sharedEntity, appDeployment) {
      const hostIdIndex =
        this.dirtyAppDeploymentSharedEntityComputeHostIds.indexOf(
          appDeployment.compute_host_id,
        );
      if (hostIdIndex >= 0) {
        this.dirtyAppDeploymentSharedEntityComputeHostIds.splice(
          hostIdIndex,
          1,
        );
      }
    },
    replaceAppDeploymentSharedEntity(sharedEntity, appDeployment) {
      this.appDeploymentsSharedEntities[appDeployment.compute_host_id] =
        sharedEntity;
    },
    setCurrentDeploymentFromAppDeploymentId(appDeploymentId) {
      this.currentDeployment = this.appDeployments.find(
        (dep) => dep.app_deployment_id === appDeploymentId,
      );
      if (!this.currentDeployment) {
        throw new Error(
          "Unable to find deployment from appDeploymentId=" + appDeploymentId,
        );
      }
      return Promise.resolve(this.currentDeployment);
    },
    setCurrentDeploymentFromComputeHostId(computeHostId) {
      this.currentDeployment = this.appDeployments.find(
        (dep) => dep.compute_host_id === computeHostId,
      );
      if (!this.currentDeployment) {
        // Create a new deployment
        const deployment = new models.ApplicationDeploymentDescription({
          user_has_write_access: true,
        });
        deployment.app_module_id = this.id;
        deployment.compute_host_id = computeHostId;
        this.currentDeployment = deployment;
        this.appDeployments.push(deployment);
        this.setApplicationDeploymentDirty(deployment);
        this.appDeploymentsSharedEntities[computeHostId] =
          new models.SharedEntity();
      }
      return Promise.resolve(this.currentDeployment);
    },
    saveAll() {
      const moduleSave = this.appModuleIsDirty
        ? this.saveApplicationModule(this.appModule).catch((error) => {
            // Navigate to the route that has the error
            this.$router.push({
              name: this.id ? "application_module" : "new_application_module",
            });
            // Cancel the chain of promises
            return Promise.reject(error);
          })
        : Promise.resolve(this.appModule);
      const interfaceSave = moduleSave.then(() =>
        this.appInterfaceIsDirty
          ? this.saveApplicationInterface(this.appInterface).catch((error) => {
              // Navigate to the route that has the error
              this.$router.push({
                name: "application_interface",
              });
              // Cancel the chain of promises
              return Promise.reject(error);
            })
          : Promise.resolve(this.appInterface),
      );
      interfaceSave
        .then(() => {
          return Promise.all(
            this.dirtyAppDeploymentComputeHostIds.map((computeHostId) => {
              const deployment = this.appDeployments.find(
                (dep) => dep.compute_host_id === computeHostId,
              );
              return this.saveApplicationDeployment(deployment).catch(
                (error) => {
                  // Navigate to the route that has the error
                  if (deployment.app_deployment_id) {
                    this.$router.push({
                      name: "application_deployment",
                      params: {
                        id: this.id,
                        deploymentId: deployment.app_deployment_id,
                      },
                    });
                  } else {
                    this.$router.push({
                      name: "new_application_deployment",
                      params: {
                        id: this.id,
                        hostId: deployment.compute_host_id,
                      },
                    });
                  }
                  return Promise.reject(error);
                },
              );
            }),
          );
        })
        .then(() => {
          return Promise.all(
            this.dirtyAppDeploymentSharedEntityComputeHostIds.map(
              (computeHostId) => {
                const sharedEntity =
                  this.appDeploymentsSharedEntities[computeHostId];
                const deployment = this.appDeployments.find(
                  (dep) => dep.compute_host_id === computeHostId,
                );
                return this.saveSharedEntity(sharedEntity, deployment).catch(
                  (error) => {
                    // Navigate to the route that has the error
                    if (deployment.app_deployment_id) {
                      this.$router.push({
                        name: "application_deployment",
                        params: {
                          id: this.id,
                          deploymentId: deployment.app_deployment_id,
                        },
                      });
                    } else {
                      this.$router.push({
                        name: "new_application_deployment",
                        params: {
                          id: this.id,
                          hostId: deployment.compute_host_id,
                        },
                      });
                    }
                    return Promise.reject(error);
                  },
                );
              },
            ),
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
          if (!this.id && this.appModule.app_module_id) {
            // if we just create a new module, navigate to app module route now
            // that we have an id
            this.$router.push({
              name: "application_module",
              params: { id: this.appModule.app_module_id },
            });
          }
          if (this.hostId) {
            // If creating a new deployment, navigate to the deployments list
            this.$router.push({
              name: "application_deployments",
              params: { id: this.appModule.app_module_id },
            });
          } else {
            // Reinitialize deployment editing so that deployment being edited is
            // the saved instance
            this.initializeDeploymentEditing();
          }
        });
    },
    cancel() {
      this.$router.push({ path: "/applications" });
    },
    onUnsavedChangesConfirmed() {
      // Continue the navigation deferred in beforeRouteLeave.
      if (this.pendingNavigation) {
        const next = this.pendingNavigation;
        this.pendingNavigation = null;
        next();
      }
    },
    deleteApplication() {
      const deleteAllDeployments = this.appDeployments.map((dep) =>
        this.deleteApplicationDeployment(dep),
      );
      return Promise.all(deleteAllDeployments)
        .then(() => this.deleteApplicationInterface(this.appInterface))
        .then(() => this.deleteApplicationModule(this.appModule))
        .then(() => {
          this.$router.push({ path: "/applications" });
        });
    },
  },
  watch: {
    $route: function (to, from) {
      if (to.params.id !== from.params.id) {
        this.initialize();
      }
      this.initializeDeploymentEditing();
    },
  },
  beforeRouteLeave(to, from, next) {
    if (this.isDirty) {
      this.pendingNavigation = next;
      this.$refs.unsavedChangesDialog.show();
    } else {
      next();
    }
  },
};
</script>
