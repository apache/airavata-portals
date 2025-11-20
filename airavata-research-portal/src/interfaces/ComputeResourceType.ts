export interface BatchQueue {
  queueName: string;
  queueDescription?: string;
  maxRunTime?: number;
  maxNodes?: number;
  maxProcessors?: number;
  maxJobsInQueue?: number;
  maxMemory?: number;
  cpuPerNode?: number;
  defaultNodeCount?: number;
  defaultCPUCount?: number;
  defaultWalltime?: number;
  queueSpecificMacros?: string;
  isDefaultQueue?: boolean;
}

export interface ComputeResource {
  computeResourceId?: string;
  hostName: string;
  hostAliases?: string[];
  ipAddresses?: string[];
  resourceDescription?: string;
  enabled?: boolean;
  batchQueues?: BatchQueue[];
  fileSystems?: Record<string, string>;
  maxMemoryPerNode?: number;
  gatewayUsageReporting?: boolean;
  gatewayUsageModuleLoadCommand?: string;
  gatewayUsageExecutable?: string;
  cpusPerNode?: number;
  defaultNodeCount?: number;
  defaultCPUCount?: number;
  defaultWalltime?: number;
}

export interface ResourceName {
  id: string;
  name: string;
}



