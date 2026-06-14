import { createPinia, defineStore, setActivePinia } from "pinia";
import { errors, services, utils } from "django-airavata-api";

// The web components are independent Vue 3 apps (custom elements) that each need
// to share a single store instance, as they did under Vuex (a single shared
// `Vuex.Store`). A module-level Pinia is created and activated so that calling
// `useExperimentStore()` from any web component returns the same singleton store,
// without requiring an `app.use(pinia)` install per custom element.
const pinia = createPinia();
setActivePinia(pinia);

export { pinia };

const PROMISES = {
  workspacePreferences: null,
};
let groupResourceProfileIdIsSet = false;
let resourceHostIdIsSet = false;
let queueSettingsAreSet = false;
let applicationModuleIdIsSet = false;

// For non-experiment editing case, need to defer compute resource settings
// initialization until each components' settings have been set
const areAllComputeResourceSettingsSet = () =>
  groupResourceProfileIdIsSet &&
  resourceHostIdIsSet &&
  queueSettingsAreSet &&
  applicationModuleIdIsSet;

// Pinia store replacing the Vuex web-component store. Pinia has no mutations, so
// the former mutations are folded into actions (state assignment is done directly
// on `this`). Getters are preserved as Pinia getters (including the function-
// returning getters which Pinia supports).
export const useExperimentStore = defineStore("experiment", {
  state: () => ({
    experiment: null,
    projects: null,
    computeResourceNames: {},
    applicationDeployments: [],
    groupResourceProfiles: null,
    applicationModuleId: null,
    appDeploymentQueues: [],
    workspacePreferences: null,
    // These state variables are to enable using UI components outside of a
    // normal experiment editing context
    queueName: null,
    nodeCount: null,
    totalCPUCount: null,
    wallTimeLimit: null,
    totalPhysicalMemory: null,
    groupResourceProfileId: null,
    resourceHostId: null,
    applicationInterface: null,
  }),
  getters: {
    getExperimentInputByName: (state) => (name) => {
      if (!state.experiment) {
        return null;
      }
      const experimentInputs = state.experiment.experiment_inputs;
      if (experimentInputs) {
        for (const experimentInput of experimentInputs) {
          if (experimentInput.name === name) {
            return experimentInput;
          }
        }
      }
      return null;
    },
    defaultProjectId: (state) =>
      state.workspacePreferences
        ? state.workspacePreferences.most_recent_project_id
        : null,
    defaultGroupResourceProfileId: (state) =>
      state.workspacePreferences
        ? state.workspacePreferences.most_recent_group_resource_profile_id
        : null,
    defaultComputeResourceId: (state) =>
      state.workspacePreferences
        ? state.workspacePreferences.most_recent_compute_resource_id
        : null,
    getGroupResourceProfileId: (state) =>
      state.experiment
        ? state.experiment.user_configuration_data.group_resource_profile_id
        : state.groupResourceProfileId,
    findGroupResourceProfile: (state) => (groupResourceProfileId) =>
      state.groupResourceProfiles
        ? state.groupResourceProfiles.find(
            (g) => g.group_resource_profile_id === groupResourceProfileId,
          )
        : null,
    groupResourceProfile() {
      return this.findGroupResourceProfile(this.getGroupResourceProfileId);
    },
    getResourceHostId: (state) =>
      state.experiment &&
      state.experiment.user_configuration_data &&
      state.experiment.user_configuration_data.computational_resource_scheduling
        ? state.experiment.user_configuration_data
            .computational_resource_scheduling.resource_host_id
        : state.resourceHostId,
    computeResources: (state) =>
      state.applicationDeployments.map((dep) => dep.compute_host_id),
    applicationDeployment() {
      if (this.applicationDeployments && this.getResourceHostId) {
        return this.applicationDeployments.find(
          (ad) => ad.compute_host_id === this.getResourceHostId,
        );
      } else {
        return null;
      }
    },
    isQueueInComputeResourcePolicy() {
      return (queueName) => {
        if (!this.computeResourcePolicy) {
          return true;
        }
        return this.computeResourcePolicy.allowed_batch_queues.includes(
          queueName,
        );
      };
    },
    queues(state) {
      return state.appDeploymentQueues
        ? state.appDeploymentQueues.filter((q) =>
            this.isQueueInComputeResourcePolicy(q.queue_name),
          )
        : [];
    },
    defaultQueue() {
      const defaultQueue = this.queues.find((q) => q.is_default_queue);
      if (defaultQueue) {
        return defaultQueue;
      } else if (this.queues.length > 0) {
        return this.queues[0];
      } else {
        return null;
      }
    },
    getQueueName: (state) => {
      return state.experiment &&
        state.experiment.user_configuration_data &&
        state.experiment.user_configuration_data
          .computational_resource_scheduling
        ? state.experiment.user_configuration_data
            .computational_resource_scheduling.queue_name
        : state.queueName;
    },
    getTotalCPUCount: (state) => {
      return state.experiment &&
        state.experiment.user_configuration_data &&
        state.experiment.user_configuration_data
          .computational_resource_scheduling
        ? state.experiment.user_configuration_data
            .computational_resource_scheduling.total_cpu_count
        : state.totalCPUCount;
    },
    getNodeCount: (state) => {
      return state.experiment &&
        state.experiment.user_configuration_data &&
        state.experiment.user_configuration_data
          .computational_resource_scheduling
        ? state.experiment.user_configuration_data
            .computational_resource_scheduling.node_count
        : state.nodeCount;
    },
    getWallTimeLimit: (state) => {
      return state.experiment &&
        state.experiment.user_configuration_data &&
        state.experiment.user_configuration_data
          .computational_resource_scheduling
        ? state.experiment.user_configuration_data
            .computational_resource_scheduling.wall_time_limit
        : state.wallTimeLimit;
    },
    getTotalPhysicalMemory: (state) => {
      return state.experiment &&
        state.experiment.user_configuration_data &&
        state.experiment.user_configuration_data
          .computational_resource_scheduling
        ? state.experiment.user_configuration_data
            .computational_resource_scheduling.total_physical_memory
        : state.totalPhysicalMemory;
    },
    queue() {
      return this.queues && this.getQueueName
        ? this.queues.find((q) => q.queue_name === this.getQueueName)
        : null;
    },
    getDefaultCPUCount() {
      return (queue) => {
        const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
        if (batchQueueResourcePolicy) {
          return Math.min(
            batchQueueResourcePolicy.max_allowed_cores,
            queue.default_cpu_count,
          );
        }
        return queue.default_cpu_count;
      };
    },
    getDefaultNodeCount() {
      return (queue) => {
        const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
        if (batchQueueResourcePolicy) {
          return Math.min(
            batchQueueResourcePolicy.max_allowed_nodes,
            queue.default_node_count,
          );
        }
        return queue.default_node_count;
      };
    },
    getDefaultWalltime() {
      return (queue) => {
        const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
        if (batchQueueResourcePolicy) {
          return Math.min(
            batchQueueResourcePolicy.max_allowed_walltime,
            queue.default_walltime,
          );
        }
        return queue.default_walltime;
      };
    },
    computeResourcePolicy() {
      if (!this.groupResourceProfile || !this.getResourceHostId) {
        return null;
      }
      return this.groupResourceProfile.compute_resource_policies.find(
        (crp) => crp.compute_resource_id === this.getResourceHostId,
      );
    },
    batchQueueResourcePolicies() {
      if (!this.groupResourceProfile || !this.getResourceHostId) {
        return null;
      }
      return this.groupResourceProfile.batch_queue_resource_policies.filter(
        (bqrp) => bqrp.compute_resource_id === this.getResourceHostId,
      );
    },
    batchQueueResourcePolicy() {
      if (!this.batchQueueResourcePolicies || !this.getQueueName) {
        return null;
      }
      return this.batchQueueResourcePolicies.find(
        (bqrp) => bqrp.queuename === this.getQueueName,
      );
    },
    maxAllowedCores() {
      if (!this.queue) {
        return 0;
      }
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_cores,
          this.queue.max_processors,
        );
      }
      return this.queue.max_processors;
    },
    maxAllowedNodes() {
      if (!this.queue) {
        return 0;
      }
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_nodes,
          this.queue.max_nodes,
        );
      }
      return this.queue.max_nodes;
    },
    maxAllowedWalltime() {
      if (!this.queue) {
        return 0;
      }
      const batchQueueResourcePolicy = this.batchQueueResourcePolicy;
      if (batchQueueResourcePolicy) {
        return Math.min(
          batchQueueResourcePolicy.max_allowed_walltime,
          this.queue.max_run_time,
        );
      }
      return this.queue.max_run_time;
    },
    maxMemory() {
      return this.queue ? this.queue.max_memory : 0;
    },
    showQueueSettings: (state) =>
      state.applicationInterface
        ? state.applicationInterface.show_queue_settings
        : false,
  },
  actions: {
    async loadNewExperiment({ applicationId }) {
      const applicationModule =
        await services.ApplicationModuleService.retrieve({
          lookup: applicationId,
        });
      const applicationInterface = await this.initializeApplicationInterface({
        applicationModuleId: applicationId,
      });
      const experiment = applicationInterface.createExperiment();
      const currentDate = new Date().toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
      });
      experiment.experiment_name = `${applicationModule.app_module_name} on ${currentDate}`;
      this.applicationModuleId = applicationId;
      applicationModuleIdIsSet = true;
      await this.setExperiment({ experiment });
    },
    async loadExperiment({ experimentId }) {
      const experiment = await services.ExperimentService.retrieve({
        lookup: experimentId,
      });
      const applicationInterface =
        await services.ApplicationInterfaceService.retrieve({
          lookup: experiment.execution_id,
        });
      this.applicationInterface = applicationInterface;
      this.applicationModuleId = applicationInterface.applicationModuleId;
      applicationModuleIdIsSet = true;
      await this.setExperiment({ experiment });
    },
    async setExperiment({ experiment }) {
      this.experiment = experiment;
      await this.loadExperimentData();
      // Check lazy experiment state properties and apply them
      if (this.queueName) {
        this.updateQueueName({ queueName: this.queueName });
      }
    },
    async loadExperimentData() {
      await Promise.all([
        this.loadProjects(),
        this.loadWorkspacePreferences(),
        this.loadGroupResourceProfiles(),
      ]);

      if (!this.experiment.project_id) {
        this.experiment.project_id =
          this.workspacePreferences.most_recent_project_id;
      }

      // Since experiment is set, all of the compute resource settings are now
      // assumed to be initialized so we can do the cross component initialization
      this.initializeComputeResourceSettings();
    },
    async initializeComputeResourceSettings() {
      // This method initializes GroupResourceProfile, ApplicationDeployments and
      // Queue settings at once since there they are interdependent.
      // This method should only be called after groupResourceProfileId,
      // resourceHostId, queue settings and applicationModuleId are all set (see
      // areAllComputeResourceSettingsSet).

      await this.initializeGroupResourceProfile();
      // applicationInterface is initialized already when creating/editing an
      // experiment but needs to be done explicitly when using other web
      // components standalone
      await this.initializeApplicationInterface({
        applicationModuleId: this.applicationModuleId,
      });
      const groupResourceProfileId = this.getGroupResourceProfileId;
      // If there is a group resource profile, load additional necessary
      // data and re-apply group resource profile
      if (groupResourceProfileId) {
        await this.loadApplicationDeployments();
        await this.loadAppDeploymentQueues();
        await this.applyGroupResourceProfile();
      }
    },
    async initializeApplicationInterface({ applicationModuleId }) {
      const applicationInterface =
        await services.ApplicationModuleService.getApplicationInterface({
          lookup: applicationModuleId,
        });
      this.applicationInterface = applicationInterface;
      return applicationInterface;
    },
    async initializeGroupResourceProfile() {
      await this.loadGroupResourceProfiles();
      await this.loadWorkspacePreferences();
      let result = this.getGroupResourceProfileId;

      if (
        !this.getGroupResourceProfileId ||
        !this.findGroupResourceProfile(this.getGroupResourceProfileId)
      ) {
        // Figure out a default value for groupResourceProfileId
        if (
          this.findGroupResourceProfile(
            this.workspacePreferences.most_recent_group_resource_profile_id,
          )
        ) {
          result =
            this.workspacePreferences.most_recent_group_resource_profile_id;
        } else if (this.groupResourceProfiles.length > 0) {
          result = this.groupResourceProfiles[0].group_resource_profile_id;
        } else {
          result = null;
        }
      }
      if (this.experiment) {
        this.experiment.user_configuration_data.group_resource_profile_id =
          result;
      } else {
        this.groupResourceProfileId = result;
        groupResourceProfileIdIsSet = true;
      }
    },
    async initializeGroupResourceProfileId({ groupResourceProfileId }) {
      this.groupResourceProfileId = groupResourceProfileId;
      groupResourceProfileIdIsSet = true;
      // only for non-experiment loading case do we call initializeComputeResourceSettings
      if (!this.experiment && areAllComputeResourceSettingsSet()) {
        this.initializeComputeResourceSettings();
      }
    },
    updateExperimentName({ name }) {
      this.experiment.experiment_name = name;
    },
    updateExperimentInputValue({ inputName, value }) {
      const experimentInput = this.experiment.experiment_inputs.find(
        (i) => i.name === inputName,
      );
      experimentInput.value = value;
    },
    updateProjectId({ projectId }) {
      this.experiment.project_id = projectId;
    },
    async updateGroupResourceProfileId({ groupResourceProfileId }) {
      const oldValue = this.getGroupResourceProfileId;
      if (this.experiment) {
        this.experiment.user_configuration_data.group_resource_profile_id =
          groupResourceProfileId;
      } else {
        this.groupResourceProfileId = groupResourceProfileId;
        groupResourceProfileIdIsSet = true;
      }
      if (groupResourceProfileId && oldValue !== groupResourceProfileId) {
        await this.loadApplicationDeployments();
        await this.applyGroupResourceProfile();
      }
    },
    async updateComputeResourceHostId({ resourceHostId }) {
      if (this.getResourceHostId !== resourceHostId) {
        if (this.experiment) {
          this.experiment.user_configuration_data.computational_resource_scheduling.resource_host_id =
            resourceHostId;
        } else {
          this.resourceHostId = resourceHostId;
          resourceHostIdIsSet = true;
        }
        await this.loadAppDeploymentQueues();
        await this.setDefaultQueue();
      }
    },
    async initializeQueueSettings({
      queueName,
      nodeCount,
      totalCPUCount,
      wallTimeLimit,
      totalPhysicalMemory,
    }) {
      this.queueName = queueName;
      // Assume all queue settings are initialized at once
      queueSettingsAreSet = true;
      this.nodeCount = nodeCount;
      this.totalCPUCount = totalCPUCount;
      this.wallTimeLimit = wallTimeLimit;
      this.totalPhysicalMemory = totalPhysicalMemory;

      // only for non-experiment loading case do we call initializeComputeResourceSettings
      if (!this.experiment && areAllComputeResourceSettingsSet()) {
        this.initializeComputeResourceSettings();
      }
    },
    updateQueueName({ queueName }) {
      if (this.experiment) {
        this.experiment.user_configuration_data.computational_resource_scheduling.queue_name =
          queueName;
      } else {
        this.queueName = queueName;
        // Assume all queue settings are initialized at once
        queueSettingsAreSet = true;
      }
      this.initializeQueue();
    },
    updateTotalCPUCount({ totalCPUCount, enableNodeCountToCpuCheck }) {
      if (this.experiment) {
        this.experiment.user_configuration_data.computational_resource_scheduling.total_cpu_count =
          totalCPUCount;
      } else {
        this.totalCPUCount = totalCPUCount;
      }
      if (enableNodeCountToCpuCheck && this.queue.cpu_per_node > 0) {
        const totalCPUCountInt = parseInt(totalCPUCount);
        const nodeCount = Math.min(
          Math.ceil(totalCPUCountInt / this.queue.cpu_per_node),
          this.maxAllowedNodes,
        );
        if (this.experiment) {
          this.experiment.user_configuration_data.computational_resource_scheduling.node_count =
            nodeCount;
        } else {
          this.nodeCount = nodeCount;
        }
      }
    },
    updateNodeCount({ nodeCount, enableNodeCountToCpuCheck }) {
      if (this.experiment) {
        this.experiment.user_configuration_data.computational_resource_scheduling.node_count =
          nodeCount;
      } else {
        this.nodeCount = nodeCount;
      }
      if (enableNodeCountToCpuCheck && this.queue.cpu_per_node > 0) {
        const nodeCountInt = parseInt(nodeCount);
        const totalCPUCount = Math.min(
          nodeCountInt * this.queue.cpu_per_node,
          this.maxAllowedCores,
        );
        if (this.experiment) {
          this.experiment.user_configuration_data.computational_resource_scheduling.total_cpu_count =
            totalCPUCount;
        } else {
          this.totalCPUCount = totalCPUCount;
        }
      }
    },
    updateWallTimeLimit({ wallTimeLimit }) {
      if (this.experiment) {
        this.experiment.user_configuration_data.computational_resource_scheduling.wall_time_limit =
          wallTimeLimit;
      } else {
        this.wallTimeLimit = wallTimeLimit;
      }
    },
    updateTotalPhysicalMemory({ totalPhysicalMemory }) {
      if (this.experiment) {
        this.experiment.user_configuration_data.computational_resource_scheduling.total_physical_memory =
          totalPhysicalMemory;
      } else {
        this.totalPhysicalMemory = totalPhysicalMemory;
      }
    },
    async loadApplicationDeployments() {
      const applicationDeployments =
        await services.ApplicationDeploymentService.list(
          {
            appModuleId: this.applicationModuleId,
            groupResourceProfileId: this.getGroupResourceProfileId,
          },
          { ignoreErrors: true },
        )
          .catch((error) => {
            // Ignore unauthorized errors, force user to pick another GroupResourceProfile
            if (!errors.ErrorUtils.isUnauthorizedError(error)) {
              return Promise.reject(error);
            } else {
              return Promise.resolve([]);
            }
          })
          // Report all other error types
          .catch(utils.FetchUtils.reportError);
      this.applicationDeployments = applicationDeployments;
    },
    async applyGroupResourceProfile() {
      // Make sure that resource host id is in the list of app deployments
      const computeResourceChanged = await this.initializeResourceHostId();
      if (computeResourceChanged) {
        await this.loadAppDeploymentQueues();
        await this.setDefaultQueue();
      } else if (!this.queue) {
        // allowed queues may have changed. If selected queue isn't in the list
        // of allowed queues, reset to the default
        await this.setDefaultQueue();
      } else {
        // reapply batchQueueResourcePolicy maximums since they may have changed
        this.applyBatchQueueResourcePolicy();
      }
    },
    async initializeComputeResources({
      applicationModuleId,
      resourceHostId = null,
    }) {
      this.applicationModuleId = applicationModuleId;
      applicationModuleIdIsSet = true;
      this.resourceHostId = resourceHostId;
      resourceHostIdIsSet = true;
      // only for non-experiment loading case do we call initializeComputeResourceSettings
      if (!this.experiment && areAllComputeResourceSettingsSet()) {
        this.initializeComputeResourceSettings();
      }
    },
    async initializeResourceHostId() {
      // if there isn't a selected compute resource or there is but it isn't in
      // the list of app deployments, set a default one
      // Returns true if the resourceHostId changed
      if (
        !this.getResourceHostId ||
        !this.computeResources.find((crid) => crid === this.getResourceHostId)
      ) {
        const defaultResourceHostId = await this.getDefaultResourceHostId();
        if (this.experiment) {
          this.experiment.user_configuration_data.computational_resource_scheduling.resource_host_id =
            defaultResourceHostId;
        } else {
          this.resourceHostId = defaultResourceHostId;
          resourceHostIdIsSet = true;
        }
        return true;
      }
      return false;
    },
    async getDefaultResourceHostId() {
      await this.loadDefaultComputeResourceId();
      if (
        this.defaultComputeResourceId &&
        this.computeResources.find(
          (crid) => crid === this.defaultComputeResourceId,
        )
      ) {
        return this.defaultComputeResourceId;
      } else if (this.computeResources.length > 0) {
        // Just pick the first one
        return this.computeResources[0];
      } else {
        return null;
      }
    },
    async loadDefaultComputeResourceId() {
      await this.loadWorkspacePreferences();
    },
    async loadAppDeploymentQueues() {
      const applicationDeployment = this.applicationDeployment;
      if (applicationDeployment) {
        const appDeploymentQueues =
          await services.ApplicationDeploymentService.getQueues({
            lookup: applicationDeployment.app_deployment_id,
          });
        this.appDeploymentQueues = appDeploymentQueues;
      } else {
        this.appDeploymentQueues = [];
      }
    },
    async setDefaultQueue() {
      // set to the default queue or the first one
      const defaultQueue = this.defaultQueue;
      if (defaultQueue) {
        this.updateQueueName({ queueName: defaultQueue.queue_name });
      } else {
        this.updateQueueName({ queueName: null });
      }
    },
    initializeQueue() {
      const queue = this.queue;
      if (queue) {
        if (this.experiment) {
          this.experiment.user_configuration_data.computational_resource_scheduling.total_cpu_count =
            this.getDefaultCPUCount(queue);
          this.experiment.user_configuration_data.computational_resource_scheduling.node_count =
            this.getDefaultNodeCount(queue);
          this.experiment.user_configuration_data.computational_resource_scheduling.wall_time_limit =
            this.getDefaultWalltime(queue);
          this.experiment.user_configuration_data.computational_resource_scheduling.total_physical_memory = 0;
        } else {
          this.totalCPUCount = this.getDefaultCPUCount(queue);
          this.nodeCount = this.getDefaultNodeCount(queue);
          this.wallTimeLimit = this.getDefaultWalltime(queue);
          this.totalPhysicalMemory = 0;
        }
      } else {
        if (this.experiment) {
          this.experiment.user_configuration_data.computational_resource_scheduling.total_cpu_count = 0;
          this.experiment.user_configuration_data.computational_resource_scheduling.node_count = 0;
          this.experiment.user_configuration_data.computational_resource_scheduling.wall_time_limit = 0;
          this.experiment.user_configuration_data.computational_resource_scheduling.total_physical_memory = 0;
        } else {
          this.totalCPUCount = 0;
          this.nodeCount = 0;
          this.wallTimeLimit = 0;
          this.totalPhysicalMemory = 0;
        }
      }
    },
    applyBatchQueueResourcePolicy() {
      if (this.batchQueueResourcePolicy) {
        const crs =
          this.experiment.user_configuration_data
            .computational_resource_scheduling;
        const totalCPUCount = Math.min(
          crs.total_cpu_count,
          this.batchQueueResourcePolicy.max_allowed_cores,
        );
        if (totalCPUCount !== crs.total_cpu_count) {
          this.totalCPUCount = totalCPUCount;
        }
        const nodeCount = Math.min(
          crs.node_count,
          this.batchQueueResourcePolicy.max_allowed_nodes,
        );
        if (nodeCount !== crs.node_count) {
          this.nodeCount = nodeCount;
        }
        const wallTimeLimit = Math.min(
          crs.wall_time_limit,
          this.batchQueueResourcePolicy.max_allowed_walltime,
        );
        if (wallTimeLimit !== crs.wall_time_limit) {
          this.wallTimeLimit = wallTimeLimit;
        }
      }
    },
    async saveExperiment() {
      if (this.experiment.experiment_id) {
        const experiment = await services.ExperimentService.update({
          data: this.experiment,
          lookup: this.experiment.experiment_id,
        });
        this.experiment = experiment;
      } else {
        const experiment = await services.ExperimentService.create({
          data: this.experiment,
        });
        this.experiment = experiment;
      }
    },
    async launchExperiment() {
      await services.ExperimentService.launch({
        lookup: this.experiment.experiment_id,
      });
    },
    async loadProjects() {
      if (!PROMISES.projects) {
        PROMISES.projects = services.ProjectService.listAll();
      }
      const projects = await PROMISES.projects;
      this.projects = projects;
    },
    async loadWorkspacePreferences() {
      if (!PROMISES.workspacePreferences) {
        PROMISES.workspacePreferences =
          services.WorkspacePreferencesService.get();
      }
      const workspacePreferences = await PROMISES.workspacePreferences;
      this.workspacePreferences = workspacePreferences;
    },
    async loadDefaultProjectId() {
      await this.loadWorkspacePreferences();
    },
    async loadComputeResourceNames() {
      const computeResourceNames =
        await services.ComputeResourceService.names();
      this.computeResourceNames = computeResourceNames;
    },
    async loadDefaultGroupResourceProfileId() {
      await this.loadWorkspacePreferences();
    },
    async loadGroupResourceProfiles() {
      if (!PROMISES.groupResourceProfiles) {
        PROMISES.groupResourceProfiles =
          services.GroupResourceProfileService.list();
      }
      const groupResourceProfiles = await PROMISES.groupResourceProfiles;
      this.groupResourceProfiles = groupResourceProfiles;
    },
  },
});

export default useExperimentStore;
