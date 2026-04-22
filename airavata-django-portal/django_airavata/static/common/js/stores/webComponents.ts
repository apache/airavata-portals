/**
 * Pinia webComponents store — ports the standalone Vuex store from:
 *   apps/workspace/static/django_airavata_workspace/js/web-components/store.js
 *
 * This store is consumed by the compute-resource web-components (ExperimentEditor,
 * QueueSettingsEditor, ComputeResourceSelector, etc.).
 *
 * Vuex store stays in place for M3; this store coexists. Consumer migration
 * happens in M4.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { errors, services, utils } from "django-airavata-api";
import type {
  Experiment,
  WorkspacePreferences,
  ApplicationDeployment,
  AppDeploymentQueue,
} from "../types/experiment";

// ---------------------------------------------------------------------------
// Module-level promise cache — mirrors the Vuex PROMISES object pattern.
// Promises are reset when the store is reset (i.e., not persisted beyond store
// lifecycle). This avoids duplicate concurrent requests.
// ---------------------------------------------------------------------------
let _cachedProjects: Promise<unknown> | null = null;
let _cachedWorkspacePreferences: Promise<unknown> | null = null;
let _cachedGroupResourceProfiles: Promise<unknown> | null = null;

// Flags for "are all compute resource settings set" check
let _groupResourceProfileIdIsSet = false;
let _resourceHostIdIsSet = false;
let _queueSettingsAreSet = false;
let _applicationModuleIdIsSet = false;

function _areAllComputeResourceSettingsSet(): boolean {
  return (
    _groupResourceProfileIdIsSet &&
    _resourceHostIdIsSet &&
    _queueSettingsAreSet &&
    _applicationModuleIdIsSet
  );
}

export const useWebComponentsStore = defineStore("webComponents", () => {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const experiment = ref<Experiment | null>(null);
  const projects = ref<unknown[] | null>(null);
  const computeResourceNames = ref<Record<string, string>>({});
  const applicationDeployments = ref<ApplicationDeployment[]>([]);
  const groupResourceProfiles = ref<unknown[] | null>(null);
  const applicationModuleId = ref<string | null>(null);
  const appDeploymentQueues = ref<AppDeploymentQueue[]>([]);
  const workspacePreferences = ref<WorkspacePreferences | null>(null);
  const applicationInterface = ref<unknown | null>(null);
  // Standalone (non-experiment) state variables
  const queueName = ref<string | null>(null);
  const nodeCount = ref<number | null>(null);
  const totalCPUCount = ref<number | null>(null);
  const wallTimeLimit = ref<number | null>(null);
  const totalPhysicalMemory = ref<number | null>(null);
  const groupResourceProfileId = ref<string | null>(null);
  const resourceHostId = ref<string | null>(null);

  // ---------------------------------------------------------------------------
  // Helpers — access experiment's nested paths
  // ---------------------------------------------------------------------------
  function _getExp(): any {
    return experiment.value as any;
  }

  function _crs(): any {
    return _getExp()?.user_configuration_data?.computational_resource_scheduling ?? null;
  }

  // ---------------------------------------------------------------------------
  // Getters
  // ---------------------------------------------------------------------------
  const getExperimentInputByName = computed(
    () =>
      (name: string): unknown | null => {
        const exp = _getExp();
        if (!exp) return null;
        const inputs: any[] = exp.experiment_inputs ?? [];
        return inputs.find((i: any) => i.name === name) ?? null;
      },
  );

  const experimentGetter = computed(() => experiment.value);

  const defaultProjectId = computed<string | null>(
    () => (workspacePreferences.value as any)?.most_recent_project_id ?? null,
  );

  const defaultGroupResourceProfileId = computed<string | null>(
    () =>
      (workspacePreferences.value as any)?.most_recent_project_resource_profile_id ?? null,
  );

  const defaultComputeResourceId = computed<string | null>(
    () => (workspacePreferences.value as any)?.most_recent_compute_resource_id ?? null,
  );

  const groupResourceProfileIdGetter = computed<string | null>(
    () =>
      experiment.value
        ? (_getExp()?.user_configuration_data?.group_resource_profile_id ?? null)
        : groupResourceProfileId.value,
  );

  const findGroupResourceProfile = computed(
    () =>
      (id: string): unknown | null =>
        groupResourceProfiles.value
          ? (groupResourceProfiles.value as any[]).find(
              (g: any) => g.group_resource_profile_id === id,
            ) ?? null
          : null,
  );

  const groupResourceProfileGetter = computed(
    () => findGroupResourceProfile.value(groupResourceProfileIdGetter.value ?? "") ?? null,
  );

  const resourceHostIdGetter = computed<string | null>(() => {
    const crsVal = _crs();
    return crsVal ? (crsVal.resource_host_id ?? null) : resourceHostId.value;
  });

  const computeResources = computed<string[]>(() =>
    (applicationDeployments.value as any[]).map((dep: any) => dep.compute_host_id as string),
  );

  const applicationDeployment = computed<ApplicationDeployment | null>(() => {
    const hostId = resourceHostIdGetter.value;
    if (applicationDeployments.value.length && hostId) {
      return (
        (applicationDeployments.value as any[]).find(
          (ad: any) => ad.compute_host_id === hostId,
        ) ?? null
      );
    }
    return null;
  });

  const isQueueInComputeResourcePolicy = computed(
    () =>
      (qname: string): boolean => {
        const crp = computeResourcePolicyGetter.value;
        if (!crp) return true;
        return !!(crp as any).allowedBatchQueues?.includes(qname);
      },
  );

  const queues = computed<AppDeploymentQueue[]>(() =>
    appDeploymentQueues.value
      ? (appDeploymentQueues.value as any[]).filter((q: any) =>
          isQueueInComputeResourcePolicy.value(q.queue_name),
        )
      : [],
  );

  const defaultQueue = computed<AppDeploymentQueue | null>(() => {
    const qs = queues.value as any[];
    const dq = qs.find((q: any) => q.is_default_queue);
    return dq ?? (qs.length > 0 ? qs[0] : null);
  });

  const queueNameGetter = computed<string | null>(() => {
    const crsVal = _crs();
    return crsVal ? (crsVal.queue_name ?? null) : queueName.value;
  });

  const totalCPUCountGetter = computed<number | null>(() => {
    const crsVal = _crs();
    return crsVal ? (crsVal.total_cpu_count ?? null) : totalCPUCount.value;
  });

  const nodeCountGetter = computed<number | null>(() => {
    const crsVal = _crs();
    return crsVal ? (crsVal.node_count ?? null) : nodeCount.value;
  });

  const wallTimeLimitGetter = computed<number | null>(() => {
    const crsVal = _crs();
    return crsVal ? (crsVal.wall_time_limit ?? null) : wallTimeLimit.value;
  });

  const totalPhysicalMemoryGetter = computed<number | null>(() => {
    const crsVal = _crs();
    return crsVal ? (crsVal.total_physical_memory ?? null) : totalPhysicalMemory.value;
  });

  const queue = computed<AppDeploymentQueue | null>(
    () =>
      queues.value && queueNameGetter.value
        ? (queues.value as any[]).find(
            (q: any) => q.queue_name === queueNameGetter.value,
          ) ?? null
        : null,
  );

  const computeResourcePolicyGetter = computed<unknown | null>(() => {
    const grp = groupResourceProfileGetter.value as any;
    const hostId = resourceHostIdGetter.value;
    if (!grp || !hostId) return null;
    return (
      (grp.compute_resource_policies ?? []).find(
        (crp: any) => crp.compute_resource_id === hostId,
      ) ?? null
    );
  });

  const batchQueueResourcePolicies = computed<unknown[] | null>(() => {
    const grp = groupResourceProfileGetter.value as any;
    const hostId = resourceHostIdGetter.value;
    if (!grp || !hostId) return null;
    return (grp.batch_queue_resource_policies ?? []).filter(
      (bqrp: any) => bqrp.compute_resource_id === hostId,
    );
  });

  const batchQueueResourcePolicy = computed<unknown | null>(() => {
    const policies = batchQueueResourcePolicies.value;
    const qname = queueNameGetter.value;
    if (!policies || !qname) return null;
    return (policies as any[]).find((bqrp: any) => bqrp.queuename === qname) ?? null;
  });

  const getDefaultCPUCount = computed(
    () =>
      (q: any): number => {
        const policy = batchQueueResourcePolicy.value as any;
        return policy ? Math.min(policy.maxAllowedCores, q.default_cpu_count) : q.default_cpu_count;
      },
  );

  const getDefaultNodeCount = computed(
    () =>
      (q: any): number => {
        const policy = batchQueueResourcePolicy.value as any;
        return policy
          ? Math.min(policy.maxAllowedNodes, q.default_node_count)
          : q.default_node_count;
      },
  );

  const getDefaultWalltime = computed(
    () =>
      (q: any): number => {
        const policy = batchQueueResourcePolicy.value as any;
        return policy
          ? Math.min(policy.maxAllowedWalltime, q.default_walltime)
          : q.default_walltime;
      },
  );

  const maxAllowedCores = computed<number>(() => {
    const q = queue.value as any;
    if (!q) return 0;
    const policy = batchQueueResourcePolicy.value as any;
    return policy ? Math.min(policy.maxAllowedCores, q.max_processors) : q.max_processors;
  });

  const maxAllowedNodes = computed<number>(() => {
    const q = queue.value as any;
    if (!q) return 0;
    const policy = batchQueueResourcePolicy.value as any;
    return policy ? Math.min(policy.maxAllowedNodes, q.max_nodes) : q.max_nodes;
  });

  const maxAllowedWalltime = computed<number>(() => {
    const q = queue.value as any;
    if (!q) return 0;
    const policy = batchQueueResourcePolicy.value as any;
    return policy ? Math.min(policy.maxAllowedWalltime, q.max_run_time) : q.max_run_time;
  });

  const maxMemory = computed<number>(() => {
    const q = queue.value as any;
    return q ? (q.max_memory ?? 0) : 0;
  });

  const showQueueSettings = computed<boolean>(
    () => !!(applicationInterface.value as any)?.show_queue_settings,
  );

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  async function loadNewExperiment({ applicationId }: { applicationId: string }): Promise<void> {
    const applicationModule = (await services.ApplicationModuleService.retrieve({
      lookup: applicationId,
    })) as any;
    const iface = await initializeApplicationInterface({ applicationModuleId: applicationId });
    const exp: any = iface.createExperiment();
    const currentDate = new Date().toLocaleString([], {
      dateStyle: "medium",
      timeStyle: "short",
    });
    exp.experiment_name = `${applicationModule.app_module_name} on ${currentDate}`;
    _setApplicationModuleId({ applicationModuleId: applicationId });
    await setExperiment({ experiment: exp });
  }

  async function loadExperiment({ experimentId }: { experimentId: string }): Promise<void> {
    const exp = (await services.ExperimentService.retrieve({ lookup: experimentId })) as any;
    const iface = (await services.ApplicationInterfaceService.retrieve({
      lookup: exp.execution_id,
    })) as any;
    applicationInterface.value = iface;
    _setApplicationModuleId({ applicationModuleId: iface.application_module_id });
    await setExperiment({ experiment: exp });
  }

  async function setExperiment({ experiment: exp }: { experiment: Experiment }): Promise<void> {
    experiment.value = exp;
    await loadExperimentData();
    // Re-apply pending queue name if it was set before experiment loaded
    if (queueName.value) {
      await updateQueueName({ queueName: queueName.value });
    }
  }

  async function loadExperimentData(): Promise<void> {
    await Promise.all([loadProjects(), loadWorkspacePreferences(), loadGroupResourceProfiles()]);
    const exp = _getExp();
    if (exp && !exp.project_id) {
      exp.project_id = (workspacePreferences.value as any)?.most_recent_project_id ?? null;
    }
    await initializeComputeResourceSettings();
  }

  async function initializeComputeResourceSettings(): Promise<void> {
    await initializeGroupResourceProfile();
    await initializeApplicationInterface({ applicationModuleId: applicationModuleId.value ?? "" });
    const grpId = groupResourceProfileIdGetter.value;
    if (grpId) {
      await loadApplicationDeployments();
      await loadAppDeploymentQueues();
      await applyGroupResourceProfile();
    }
  }

  async function initializeApplicationInterface({
    applicationModuleId: modId,
  }: {
    applicationModuleId: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  }): Promise<any> {
    if (!modId) return null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const iface = (await services.ApplicationModuleService.getApplicationInterface({
      lookup: modId,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    })) as any;
    applicationInterface.value = iface;
    return iface;
  }

  async function initializeGroupResourceProfile(): Promise<void> {
    await loadGroupResourceProfiles();
    await loadWorkspacePreferences();

    let result: string | null = groupResourceProfileIdGetter.value;
    const find = findGroupResourceProfile.value;

    if (!result || !find(result)) {
      const prefs = workspacePreferences.value as any;
      if (prefs?.most_recent_project_resource_profile_id &&
          find(prefs.most_recent_project_resource_profile_id)) {
        result = prefs.most_recent_project_resource_profile_id;
      } else if ((groupResourceProfiles.value as any[] ?? []).length > 0) {
        result = (groupResourceProfiles.value as any[])[0].group_resource_profile_id;
      } else {
        result = null;
      }
    }

    if (experiment.value) {
      (_getExp()!).user_configuration_data.group_resource_profile_id = result;
    } else {
      groupResourceProfileId.value = result;
    }
  }

  async function initializeGroupResourceProfileId({
    groupResourceProfileId: id,
  }: {
    groupResourceProfileId: string;
  }): Promise<void> {
    groupResourceProfileId.value = id;
    _groupResourceProfileIdIsSet = true;
    if (!experiment.value && _areAllComputeResourceSettingsSet()) {
      await initializeComputeResourceSettings();
    }
  }

  function updateExperimentName({ name }: { name: string }): void {
    if (_getExp()) _getExp().experiment_name = name;
  }

  function updateExperimentInputValue({ inputName, value }: { inputName: string; value: unknown }): void {
    const inputs: any[] = _getExp()?.experiment_inputs ?? [];
    const input = inputs.find((i: any) => i.name === inputName);
    if (input) input.value = value;
  }

  function updateProjectId({ projectId }: { projectId: string }): void {
    if (_getExp()) _getExp().project_id = projectId;
  }

  async function updateGroupResourceProfileId({
    groupResourceProfileId: id,
  }: {
    groupResourceProfileId: string;
  }): Promise<void> {
    const old = groupResourceProfileIdGetter.value;
    if (experiment.value) {
      _getExp().user_configuration_data.group_resource_profile_id = id;
    } else {
      groupResourceProfileId.value = id;
    }
    if (id && old !== id) {
      await loadApplicationDeployments();
      await applyGroupResourceProfile();
    }
  }

  async function updateComputeResourceHostId({
    resourceHostId: id,
  }: {
    resourceHostId: string;
  }): Promise<void> {
    if (resourceHostIdGetter.value !== id) {
      if (experiment.value) {
        _crs()!.resource_host_id = id;
      } else {
        resourceHostId.value = id;
      }
      await loadAppDeploymentQueues();
      await setDefaultQueue();
    }
  }

  async function initializeQueueSettings({
    queueName: qName,
    nodeCount: nc,
    totalCPUCount: cpu,
    wallTimeLimit: wtl,
    totalPhysicalMemory: mem,
  }: {
    queueName: string;
    nodeCount: number;
    totalCPUCount: number;
    wallTimeLimit: number;
    totalPhysicalMemory: number;
  }): Promise<void> {
    _setQueueName({ queueName: qName });
    _setNodeCount({ nodeCount: nc });
    _setTotalCPUCount({ totalCPUCount: cpu });
    _setWallTimeLimit({ wallTimeLimit: wtl });
    _setTotalPhysicalMemory({ totalPhysicalMemory: mem });
    _queueSettingsAreSet = true;
    if (!experiment.value && _areAllComputeResourceSettingsSet()) {
      await initializeComputeResourceSettings();
    }
  }

  async function updateQueueName({ queueName: qName }: { queueName: string | null }): Promise<void> {
    if (experiment.value) {
      _crs()!.queue_name = qName;
    } else {
      queueName.value = qName;
    }
    initializeQueue();
  }

  function updateTotalCPUCount({
    totalCPUCount: cpu,
    enableNodeCountToCpuCheck,
  }: {
    totalCPUCount: number;
    enableNodeCountToCpuCheck?: boolean;
  }): void {
    if (experiment.value) {
      _crs()!.total_cpu_count = cpu;
    } else {
      totalCPUCount.value = cpu;
    }
    const q = queue.value as any;
    if (enableNodeCountToCpuCheck && q?.cpu_per_node > 0) {
      const nc = Math.min(Math.ceil(cpu / q.cpu_per_node), maxAllowedNodes.value);
      if (experiment.value) {
        _crs()!.node_count = nc;
      } else {
        nodeCount.value = nc;
      }
    }
  }

  function updateNodeCount({
    nodeCount: nc,
    enableNodeCountToCpuCheck,
  }: {
    nodeCount: number;
    enableNodeCountToCpuCheck?: boolean;
  }): void {
    if (experiment.value) {
      _crs()!.node_count = nc;
    } else {
      nodeCount.value = nc;
    }
    const q = queue.value as any;
    if (enableNodeCountToCpuCheck && q?.cpu_per_node > 0) {
      const cpu = Math.min(nc * q.cpu_per_node, maxAllowedCores.value);
      if (experiment.value) {
        _crs()!.total_cpu_count = cpu;
      } else {
        totalCPUCount.value = cpu;
      }
    }
  }

  function updateWallTimeLimit({ wallTimeLimit: wtl }: { wallTimeLimit: number }): void {
    if (experiment.value) {
      _crs()!.wall_time_limit = wtl;
    } else {
      wallTimeLimit.value = wtl;
    }
  }

  function updateTotalPhysicalMemory({
    totalPhysicalMemory: mem,
  }: {
    totalPhysicalMemory: number;
  }): void {
    if (experiment.value) {
      _crs()!.total_physical_memory = mem;
    } else {
      totalPhysicalMemory.value = mem;
    }
  }

  async function loadApplicationDeployments(): Promise<void> {
    const grpId = groupResourceProfileIdGetter.value;
    const deployments = (await services.ApplicationDeploymentService.list(
      {
        app_module_id: applicationModuleId.value,
        group_resource_profile_id: grpId,
      },
      { ignoreErrors: true },
    )
      .catch((error: unknown) => {
        if (!errors.ErrorUtils.isUnauthorizedError(error)) {
          return Promise.reject(error);
        }
        return Promise.resolve([]);
      })
      .catch(utils.FetchUtils.reportError)) as ApplicationDeployment[];
    applicationDeployments.value = deployments;
  }

  async function applyGroupResourceProfile(): Promise<void> {
    const computeResourceChanged = await initializeResourceHostId();
    if (computeResourceChanged) {
      await loadAppDeploymentQueues();
      await setDefaultQueue();
    } else if (!queue.value) {
      await setDefaultQueue();
    } else {
      applyBatchQueueResourcePolicy();
    }
  }

  async function initializeComputeResources({
    applicationModuleId: modId,
    resourceHostId: hostId = null,
  }: {
    applicationModuleId: string;
    resourceHostId?: string | null;
  }): Promise<void> {
    _setApplicationModuleId({ applicationModuleId: modId });
    resourceHostId.value = hostId;
    _resourceHostIdIsSet = true;
    if (!experiment.value && _areAllComputeResourceSettingsSet()) {
      await initializeComputeResourceSettings();
    }
  }

  async function initializeResourceHostId(): Promise<boolean> {
    const currentHostId = resourceHostIdGetter.value;
    const resources = computeResources.value;
    if (!currentHostId || !resources.includes(currentHostId)) {
      const defaultHostId = await getDefaultResourceHostId();
      if (experiment.value) {
        _crs()!.resource_host_id = defaultHostId;
      } else {
        resourceHostId.value = defaultHostId;
      }
      return true;
    }
    return false;
  }

  async function getDefaultResourceHostId(): Promise<string | null> {
    await loadDefaultComputeResourceId();
    const defId = defaultComputeResourceId.value;
    const resources = computeResources.value;
    if (defId && resources.includes(defId)) return defId;
    return resources.length > 0 ? resources[0] : null;
  }

  async function loadDefaultComputeResourceId(): Promise<void> {
    await loadWorkspacePreferences();
  }

  async function loadAppDeploymentQueues(): Promise<void> {
    const dep = applicationDeployment.value as any;
    if (dep) {
      const qs = (await services.ApplicationDeploymentService.getQueues({
        lookup: dep.app_deployment_id,
      })) as AppDeploymentQueue[];
      appDeploymentQueues.value = qs;
    } else {
      appDeploymentQueues.value = [];
    }
  }

  async function setDefaultQueue(): Promise<void> {
    const dq = defaultQueue.value as any;
    if (dq) {
      await updateQueueName({ queueName: dq.queue_name });
    } else {
      await updateQueueName({ queueName: null });
    }
  }

  function initializeQueue(): void {
    const q = queue.value as any;
    if (q) {
      const cpu = getDefaultCPUCount.value(q);
      const nc = getDefaultNodeCount.value(q);
      const wtl = getDefaultWalltime.value(q);
      if (experiment.value) {
        _crs()!.total_cpu_count = cpu;
        _crs()!.node_count = nc;
        _crs()!.wall_time_limit = wtl;
        _crs()!.total_physical_memory = 0;
      } else {
        totalCPUCount.value = cpu;
        nodeCount.value = nc;
        wallTimeLimit.value = wtl;
        totalPhysicalMemory.value = 0;
      }
    } else {
      if (experiment.value) {
        _crs()!.total_cpu_count = 0;
        _crs()!.node_count = 0;
        _crs()!.wall_time_limit = 0;
        _crs()!.total_physical_memory = 0;
      } else {
        totalCPUCount.value = 0;
        nodeCount.value = 0;
        wallTimeLimit.value = 0;
        totalPhysicalMemory.value = 0;
      }
    }
  }

  function applyBatchQueueResourcePolicy(): void {
    const policy = batchQueueResourcePolicy.value as any;
    if (!policy) return;
    const exp = _getExp();
    if (!exp) return;
    const crsVal = _crs()!;
    const cpu = Math.min(crsVal.total_cpu_count, policy.maxAllowedCores);
    if (cpu !== crsVal.total_cpu_count) crsVal.total_cpu_count = cpu;
    const nc = Math.min(crsVal.node_count, policy.maxAllowedNodes);
    if (nc !== crsVal.node_count) crsVal.node_count = nc;
    const wtl = Math.min(crsVal.wall_time_limit, policy.maxAllowedWalltime);
    if (wtl !== crsVal.wall_time_limit) crsVal.wall_time_limit = wtl;
  }

  async function saveExperiment(): Promise<void> {
    const exp = _getExp();
    if (!exp) return;
    if (exp.experiment_id) {
      const saved = (await services.ExperimentService.update({
        data: exp,
        lookup: exp.experiment_id,
      })) as Experiment;
      experiment.value = saved;
    } else {
      const saved = (await services.ExperimentService.create({ data: exp })) as Experiment;
      experiment.value = saved;
    }
  }

  async function launchExperiment(): Promise<void> {
    const exp = _getExp();
    if (!exp?.experiment_id) return;
    await services.ExperimentService.launch({ lookup: exp.experiment_id });
  }

  async function loadProjects(): Promise<void> {
    if (!_cachedProjects) {
      _cachedProjects = services.ProjectService.listAll();
    }
    projects.value = (await _cachedProjects) as unknown[];
  }

  async function loadWorkspacePreferences(): Promise<void> {
    if (!_cachedWorkspacePreferences) {
      _cachedWorkspacePreferences = services.WorkspacePreferencesService.get();
    }
    workspacePreferences.value = (await _cachedWorkspacePreferences) as WorkspacePreferences;
  }

  async function loadDefaultProjectId(): Promise<void> {
    await loadWorkspacePreferences();
  }

  async function loadComputeResourceNames(): Promise<void> {
    computeResourceNames.value =
      (await services.ComputeResourceService.names()) as Record<string, string>;
  }

  async function loadDefaultGroupResourceProfileId(): Promise<void> {
    await loadWorkspacePreferences();
  }

  async function loadGroupResourceProfiles(): Promise<void> {
    if (!_cachedGroupResourceProfiles) {
      _cachedGroupResourceProfiles = services.ProjectResourceProfileService.list();
    }
    groupResourceProfiles.value = (await _cachedGroupResourceProfiles) as unknown[];
  }

  // ---------------------------------------------------------------------------
  // Private helpers (internal state setters, not exposed)
  // ---------------------------------------------------------------------------
  function _setApplicationModuleId({ applicationModuleId: id }: { applicationModuleId: string }): void {
    applicationModuleId.value = id;
    _applicationModuleIdIsSet = true;
  }

  function _setQueueName({ queueName: qName }: { queueName: string }): void {
    queueName.value = qName;
  }

  function _setNodeCount({ nodeCount: nc }: { nodeCount: number }): void {
    nodeCount.value = nc;
  }

  function _setTotalCPUCount({ totalCPUCount: cpu }: { totalCPUCount: number }): void {
    totalCPUCount.value = cpu;
  }

  function _setWallTimeLimit({ wallTimeLimit: wtl }: { wallTimeLimit: number }): void {
    wallTimeLimit.value = wtl;
  }

  function _setTotalPhysicalMemory({ totalPhysicalMemory: mem }: { totalPhysicalMemory: number }): void {
    totalPhysicalMemory.value = mem;
  }

  // ---------------------------------------------------------------------------
  // Expose
  // ---------------------------------------------------------------------------
  return {
    // raw state refs (direct writes for internal use; consumers use the
    // computed getters below which resolve experiment vs standalone mode)
    projects,
    computeResourceNames,
    applicationDeployments,
    groupResourceProfiles,
    applicationModuleId,
    appDeploymentQueues,
    workspacePreferences,
    applicationInterface,
    // getters (experiment-aware; these shadow the raw refs for read access)
    getExperimentInputByName,
    experiment: experimentGetter,
    defaultProjectId,
    defaultGroupResourceProfileId,
    defaultComputeResourceId,
    groupResourceProfileId: groupResourceProfileIdGetter,
    findGroupResourceProfile,
    groupResourceProfile: groupResourceProfileGetter,
    resourceHostId: resourceHostIdGetter,
    computeResources,
    applicationDeployment,
    isQueueInComputeResourcePolicy,
    queues,
    defaultQueue,
    queueName: queueNameGetter,
    totalCPUCount: totalCPUCountGetter,
    nodeCount: nodeCountGetter,
    wallTimeLimit: wallTimeLimitGetter,
    totalPhysicalMemory: totalPhysicalMemoryGetter,
    queue,
    computeResourcePolicy: computeResourcePolicyGetter,
    batchQueueResourcePolicies,
    batchQueueResourcePolicy,
    getDefaultCPUCount,
    getDefaultNodeCount,
    getDefaultWalltime,
    maxAllowedCores,
    maxAllowedNodes,
    maxAllowedWalltime,
    maxMemory,
    showQueueSettings,
    // actions
    loadNewExperiment,
    loadExperiment,
    setExperiment,
    loadExperimentData,
    initializeComputeResourceSettings,
    initializeApplicationInterface,
    initializeGroupResourceProfile,
    initializeGroupResourceProfileId,
    updateExperimentName,
    updateExperimentInputValue,
    updateProjectId,
    updateGroupResourceProfileId,
    updateComputeResourceHostId,
    initializeQueueSettings,
    updateQueueName,
    updateTotalCPUCount,
    updateNodeCount,
    updateWallTimeLimit,
    updateTotalPhysicalMemory,
    loadApplicationDeployments,
    applyGroupResourceProfile,
    initializeComputeResources,
    initializeResourceHostId,
    getDefaultResourceHostId,
    loadDefaultComputeResourceId,
    loadAppDeploymentQueues,
    setDefaultQueue,
    initializeQueue,
    applyBatchQueueResourcePolicy,
    saveExperiment,
    launchExperiment,
    loadProjects,
    loadWorkspacePreferences,
    loadDefaultProjectId,
    loadComputeResourceNames,
    loadDefaultGroupResourceProfileId,
    loadGroupResourceProfiles,
  };
});
