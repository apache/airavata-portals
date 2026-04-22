<template>
  <div>
    <!-- Back link -->
    <div class="mb-3">
      <a href="/resources/compute" class="text-muted" style="font-size: 0.8125rem">
        <i class="fa fa-arrow-left me-1"></i>Back to Compute Resources
      </a>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <i class="fa fa-spinner fa-spin me-1"></i> Loading compute resource...
    </div>

    <div v-else-if="!resource" class="alert alert-warning">Compute resource not found.</div>

    <template v-else>
      <!-- Header -->
      <div class="row align-items-center mb-3">
        <div class="col">
          <h1 class="h4 mb-0">
            {{ (resource as Record<string, unknown>).host_name }}
            <span
              v-if="(resource as Record<string, unknown>).enabled"
              class="badge bg-success ms-2"
              style="font-size: 0.7rem; vertical-align: middle"
              >Enabled</span
            >
            <span
              v-else
              class="badge bg-secondary ms-2"
              style="font-size: 0.7rem; vertical-align: middle"
              >Disabled</span
            >
          </h1>
          <p
            v-if="(resource as Record<string, unknown>).resource_description"
            class="text-muted mb-0"
            style="font-size: 0.8125rem"
          >
            {{ (resource as Record<string, unknown>).resource_description }}
          </p>
        </div>
        <div class="col-auto d-flex gap-2">
          <button
            class="btn btn-outline-secondary btn-sm"
            :disabled="testingConnection || !sshCredentialToken"
            @click="testConnection"
          >
            <i class="fa fa-plug me-1"></i>
            <span v-if="testingConnection"
              ><i class="fa fa-spinner fa-spin me-1"></i>Testing...</span
            >
            <span v-else>Test Connection</span>
          </button>
          <button class="btn btn-outline-danger btn-sm" @click="deleteResource">
            <i class="fa fa-trash me-1"></i>Delete
          </button>
        </div>
      </div>

      <!-- Save error / success alerts -->
      <div
        v-if="saveError"
        class="alert alert-danger alert-dismissible"
        style="font-size: 0.8125rem"
      >
        {{ saveError }}
        <button type="button" class="btn-close" @click="saveError = null"></button>
      </div>
      <div
        v-if="saveSuccess"
        class="alert alert-success alert-dismissible"
        style="font-size: 0.8125rem"
      >
        Compute resource saved successfully.
        <button type="button" class="btn-close" @click="saveSuccess = false"></button>
      </div>

      <!-- Card 1: General -->
      <div class="card mb-3">
        <div class="card-header" style="font-size: 0.875rem; font-weight: 600">General</div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label form-label-sm">Host Name</label>
              <input
                v-model="(resource as Record<string, unknown>).host_name"
                type="text"
                class="form-control form-control-sm"
              />
            </div>
            <div class="col-md-6">
              <label class="form-label form-label-sm">Description</label>
              <input
                v-model="(resource as Record<string, unknown>).resource_description"
                type="text"
                class="form-control form-control-sm"
                placeholder="Optional"
              />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Enabled</label>
              <div class="form-check form-switch mt-1">
                <input
                  id="enabledSwitch"
                  v-model="(resource as Record<string, unknown>).enabled"
                  class="form-check-input"
                  type="checkbox"
                />
                <label class="form-check-label" for="enabledSwitch" style="font-size: 0.8125rem">{{
                  (resource as Record<string, unknown>).enabled ? "Yes" : "No"
                }}</label>
              </div>
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">CPUs Per Node</label>
              <input
                v-model.number="(resource as Record<string, unknown>).cpus_per_node"
                type="number"
                class="form-control form-control-sm"
                min="1"
              />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Max Memory (MB)</label>
              <input
                v-model.number="(resource as Record<string, unknown>).max_memory_per_node"
                type="number"
                class="form-control form-control-sm"
                min="0"
              />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default Node Count</label>
              <input
                v-model.number="(resource as Record<string, unknown>).default_node_count"
                type="number"
                class="form-control form-control-sm"
                min="1"
              />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default CPU Count</label>
              <input
                v-model.number="(resource as Record<string, unknown>).default_cpu_count"
                type="number"
                class="form-control form-control-sm"
                min="1"
              />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default Walltime (min)</label>
              <input
                v-model.number="(resource as Record<string, unknown>).default_walltime"
                type="number"
                class="form-control form-control-sm"
                min="1"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Card 2: Credentials -->
      <div class="card mb-3">
        <div class="card-header" style="font-size: 0.875rem; font-weight: 600">Credentials</div>
        <div class="card-body">
          <div class="mb-3">
            <label class="form-label form-label-sm">SSH Credential</label>
            <ssh-credential-selector v-model="sshCredentialToken" :null-option="true" />
          </div>

          <!-- Test connection status -->
          <div v-if="connectionStatus" class="mb-3">
            <div
              class="alert mb-2 py-2"
              :class="connectionStatus.success ? 'alert-success' : 'alert-danger'"
              style="font-size: 0.8125rem"
            >
              <i
                :class="connectionStatus.success ? 'fa fa-check-circle' : 'fa fa-times-circle'"
                class="me-1"
              ></i>
              {{ connectionStatus.message }}
            </div>
          </div>

          <!-- Test connection button -->
          <div class="d-flex gap-2 align-items-center">
            <button
              class="btn btn-outline-secondary btn-sm"
              :disabled="testingConnection || !sshCredentialToken"
              @click="testConnection"
            >
              <span v-if="testingConnection"
                ><i class="fa fa-spinner fa-spin me-1"></i>Testing...</span
              >
              <span v-else><i class="fa fa-plug me-1"></i>Test Connection</span>
            </button>

            <!-- Discover HPC Info button — shown after successful connection -->
            <button
              v-if="connectionStatus && connectionStatus.success"
              class="btn btn-outline-primary btn-sm"
              :disabled="discoveringHPC"
              @click="discoverHPCInfo"
            >
              <span v-if="discoveringHPC"
                ><i class="fa fa-spinner fa-spin me-1"></i>Discovering...</span
              >
              <span v-else><i class="fa fa-search me-1"></i>Discover HPC Info</span>
            </button>
          </div>

          <div
            v-if="discoverError"
            class="alert alert-danger mt-2 py-2"
            style="font-size: 0.8125rem"
          >
            {{ discoverError }}
          </div>
        </div>
      </div>

      <!-- Card 3: HPC Configuration (partitions) -->
      <div class="card mb-3">
        <div
          class="card-header d-flex align-items-center justify-content-between"
          style="font-size: 0.875rem; font-weight: 600"
        >
          <span>HPC Configuration</span>
          <button class="btn btn-outline-secondary btn-sm" @click="addPartitionRow">
            <i class="fa fa-plus me-1"></i>Add Partition
          </button>
        </div>
        <div class="card-body p-0">
          <div v-if="partitions.length === 0" class="table-empty p-4 text-center text-muted">
            <i
              class="fa fa-th-list table-empty__icon"
              style="font-size: 2rem; display: block; margin-bottom: 0.5rem"
            ></i>
            <div class="table-empty__title">No partitions configured</div>
            <div class="table-empty__text" style="font-size: 0.8125rem">
              Use "Add Partition" or "Discover HPC Info" after a successful SSH connection.
            </div>
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm mb-0" style="font-size: 0.8125rem">
              <thead class="table-light">
                <tr>
                  <th>Partition</th>
                  <th>Max Walltime (hrs)</th>
                  <th>Max Nodes</th>
                  <th>CPUs/Node</th>
                  <th>Memory (MB)</th>
                  <th>GPUs</th>
                  <th>GPU Types</th>
                  <th>Accounts</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(p, idx) in partitions" :key="idx">
                  <td>
                    <input
                      v-model="p.partition"
                      type="text"
                      class="form-control form-control-sm"
                      placeholder="e.g. debug"
                    />
                  </td>
                  <td>
                    <input
                      v-model.number="p.maxRunTime"
                      type="number"
                      class="form-control form-control-sm"
                      min="1"
                      style="width: 90px"
                      placeholder="hours"
                    />
                  </td>
                  <td>
                    <input
                      v-model.number="p.nodes"
                      type="number"
                      class="form-control form-control-sm"
                      min="1"
                      style="width: 80px"
                    />
                  </td>
                  <td>
                    <input
                      v-model.number="p.maxCpusPerNode"
                      type="number"
                      class="form-control form-control-sm"
                      min="1"
                      style="width: 80px"
                    />
                  </td>
                  <td>
                    <input
                      v-model.number="p.maxMemMbPerNode"
                      type="number"
                      class="form-control form-control-sm"
                      min="0"
                      style="width: 100px"
                    />
                  </td>
                  <td>
                    <input
                      v-model.number="p.maxGpusPerNode"
                      type="number"
                      class="form-control form-control-sm"
                      min="0"
                      style="width: 80px"
                    />
                  </td>
                  <td>
                    <input
                      v-model="p.gpuTypesStr"
                      type="text"
                      class="form-control form-control-sm"
                      placeholder="comma-separated"
                    />
                  </td>
                  <td>
                    <input
                      v-model="p.accountsStr"
                      type="text"
                      class="form-control form-control-sm"
                      placeholder="comma-separated"
                    />
                  </td>
                  <td>
                    <button
                      class="btn btn-link btn-sm text-danger p-0"
                      title="Remove"
                      @click="removePartitionRow(idx)"
                    >
                      <i class="fa fa-times"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Card 4: SSH Job Submission -->
      <div class="card mb-3">
        <div class="card-header" style="font-size: 0.875rem; font-weight: 600">
          SSH Job Submission
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label form-label-sm">Resource Manager</label>
              <select
                v-model="jobSubmission.resourceManagerType"
                class="form-select form-select-sm"
              >
                <option value="">-- Select --</option>
                <option value="SLURM">SLURM</option>
                <option value="PBS">PBS</option>
                <option value="LSF">LSF</option>
                <option value="UGE">UGE</option>
                <option value="HTCONDOR">HTCONDOR</option>
                <option value="FORK">FORK</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">Job Manager Bin Path</label>
              <input
                v-model="jobSubmission.jobManagerBinPath"
                type="text"
                class="form-control form-control-sm"
                placeholder="/usr/bin"
              />
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">SSH Port</label>
              <input
                v-model.number="jobSubmission.sshPort"
                type="number"
                class="form-control form-control-sm"
                min="1"
                max="65535"
                placeholder="22"
              />
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">Security Protocol</label>
              <select v-model="jobSubmission.securityProtocol" class="form-select form-select-sm">
                <option value="SSH_KEYS">SSH Keys</option>
                <option value="USERNAME_PASSWORD">Username/Password</option>
                <option value="GSI">GSI</option>
                <option value="KERBEROS">Kerberos</option>
                <option value="OAUTH">OAuth</option>
                <option value="LOCAL">Local</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">Monitor Mode</label>
              <select v-model="jobSubmission.monitorMode" class="form-select form-select-sm">
                <option value="POLL_JOB_MANAGER">Poll Job Manager</option>
                <option value="XSEDE_AMQP_SUBSCRIBE">XSEDE AMQP Subscribe</option>
                <option value="JOB_EMAIL_NOTIFICATION_MONITOR">Email Notification</option>
                <option value="CLOUD_JOB_MONITOR">Cloud Job Monitor</option>
                <option value="MONITOR_FORK">Monitor Fork</option>
                <option value="MONITOR_LOCAL">Monitor Local</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">Alternative SSH Host</label>
              <input
                v-model="jobSubmission.alternativeSshHostname"
                type="text"
                class="form-control form-control-sm"
                placeholder="Optional"
              />
            </div>
          </div>
          <div class="form-text mt-2" style="font-size: 0.75rem">
            SSH submission is saved separately from the general compute resource details.
          </div>
        </div>
      </div>

      <!-- Save button -->
      <div class="d-flex justify-content-end mb-4">
        <button class="btn btn-primary btn-sm" :disabled="saving" @click="saveResource">
          <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
          <span v-else><i class="fa fa-save me-1"></i>Save</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import { services, utils } from "django-airavata-api";
import SshCredentialSelector from "../../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

interface PartitionRow {
  partition: string;
  maxRunTime: number | null;
  nodes: number | null;
  maxCpusPerNode: number | null;
  maxMemMbPerNode: number | null;
  maxGpusPerNode: number | null;
  gpuTypesStr: string;
  accountsStr: string;
}

interface JobSubmission {
  submissionInterfaceId: string | null;
  resourceManagerType: string;
  jobManagerBinPath: string;
  sshPort: number;
  alternativeSshHostname: string;
  securityProtocol: string;
  monitorMode: string;
}

interface ConnectionStatus {
  success: boolean;
  message: string;
}

interface SseClient {
  connect(): void;
  on(_event: string, _handler: (_e: Record<string, unknown>) => void): void;
  off(_event: string, _handler: (_e: Record<string, unknown>) => void): void;
}

const props = withDefaults(defineProps<{
  computeResourceId?: string | null;
}>(), {
  computeResourceId: null,
});

const loading = ref(true);
const resource = ref<unknown>(null);
const sshCredentialToken = ref<string | null>(null);
const partitions = ref<PartitionRow[]>([]);
const jobSubmission = reactive<JobSubmission>({
  submissionInterfaceId: null,
  resourceManagerType: "",
  jobManagerBinPath: "",
  sshPort: 22,
  alternativeSshHostname: "",
  securityProtocol: "SSH_KEYS",
  monitorMode: "POLL_JOB_MANAGER",
});
const saving = ref(false);
const saveError = ref<string | null>(null);
const saveSuccess = ref(false);
const testingConnection = ref(false);
const connectionStatus = ref<ConnectionStatus | null>(null);
const connectionSessionId = ref<string | null>(null);
const discoveringHPC = ref(false);
const discoverError = ref<string | null>(null);
let sseHandler: ((_e: Record<string, unknown>) => void) | null = null;

function getSseClient(): SseClient | null {
  const u = utils as unknown as Record<string, unknown>;
  return (u.SSEClient as SseClient) || null;
}

async function loadResource(): Promise<void> {
  if (!props.computeResourceId) {
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    resource.value = await services.ComputeResourceService.retrieve({
      lookup: props.computeResourceId,
    });
    const res = resource.value as Record<string, unknown>;
    // Find the first SSH-protocol submission interface, if any.
    let sshInterfaceId: string | null = null;
    const jobSubIfaces = res.job_submission_interfaces as Array<Record<string, unknown>> | undefined;
    if (jobSubIfaces && jobSubIfaces.length > 0) {
      const sshIface = jobSubIfaces.find(
        (i) => i.job_submission_protocol === "SSH" || i.job_submission_protocol === "SSH_FORK",
      );
      if (sshIface) {
        sshInterfaceId = sshIface.job_submission_interface_id as string;
      }
    }
    // Load the SSH submission detail (separate endpoint).
    if (sshInterfaceId) {
      try {
        const fetchUtils = utils as unknown as { FetchUtils: { get(_url: string, _params: unknown): Promise<unknown> } };
        const sshDetail = await fetchUtils.FetchUtils.get("/api/job/submission/ssh", {
          id: sshInterfaceId,
        });
        if (sshDetail) {
          const sd = sshDetail as Record<string, unknown>;
          jobSubmission.submissionInterfaceId = sshInterfaceId;
          jobSubmission.sshPort = (sd.ssh_port as number) || 22;
          jobSubmission.alternativeSshHostname = (sd.alternative_ssh_host_name as string) || "";
          jobSubmission.securityProtocol = (sd.security_protocol as string) || "SSH_KEYS";
          jobSubmission.monitorMode = (sd.monitor_mode as string) || "POLL_JOB_MANAGER";
          const rjm = (sd.resource_job_manager as Record<string, unknown>) || {};
          jobSubmission.resourceManagerType = (rjm.resource_job_manager_type as string) || "";
          jobSubmission.jobManagerBinPath = (rjm.job_manager_bin_path as string) || "";
        }
      } catch (e) {
        // Non-fatal: form stays at defaults.
        console.warn("Failed to load SSH submission details", e);
      }
    }
    // Load existing batch queues as partitions.
    const batchQueues = res.batch_queues as Array<Record<string, unknown>> | undefined;
    if (batchQueues && batchQueues.length > 0) {
      partitions.value = batchQueues.map((q): PartitionRow => ({
        partition: (q.queue_name as string) || "",
        maxRunTime: (q.max_run_time as number) || null,
        nodes: (q.max_nodes as number) || null,
        maxCpusPerNode: (q.cpu_per_node as number) || null,
        maxMemMbPerNode: (q.max_memory as number) || null,
        maxGpusPerNode: null,
        gpuTypesStr: "",
        accountsStr: "",
      }));
    }
  } catch {
    resource.value = null;
  }
  loading.value = false;
}

function addPartitionRow(): void {
  partitions.value.push({
    partition: "",
    maxRunTime: null,
    nodes: null,
    maxCpusPerNode: null,
    maxMemMbPerNode: null,
    maxGpusPerNode: null,
    gpuTypesStr: "",
    accountsStr: "",
  });
}

function removePartitionRow(idx: number): void {
  partitions.value.splice(idx, 1);
}

async function testConnection(): Promise<void> {
  if (!sshCredentialToken.value) return;
  testingConnection.value = true;
  connectionStatus.value = null;
  connectionSessionId.value = null;

  const handler = (event: Record<string, unknown>): void => {
    testingConnection.value = false;
    connectionStatus.value = {
      success: event.success === true,
      message:
        (event.message as string) || (event.success ? "Connection successful." : "Connection failed."),
    };
    connectionSessionId.value = (event.session_id as string) || null;
    getSseClient()?.off("ssh_result", handler);
    sseHandler = null;
  };
  sseHandler = handler;
  const sseClient = getSseClient();
  sseClient?.connect();
  sseClient?.on("ssh_result", handler);

  const res = resource.value as Record<string, unknown>;
  try {
    const fetchUtils = utils as unknown as { FetchUtils: { post(_url: string, _data: unknown): Promise<unknown> } };
    await fetchUtils.FetchUtils.post("/api/ssh/test/", {
      compute_resource_id: props.computeResourceId,
      credential_token: sshCredentialToken.value,
      host: res.host_name,
      port: jobSubmission.sshPort || 22,
    });
  } catch (e) {
    testingConnection.value = false;
    const err = e as { message?: string };
    connectionStatus.value = {
      success: false,
      message: err?.message || "Failed to initiate connection test.",
    };
    getSseClient()?.off("ssh_result", handler);
    sseHandler = null;
  }
}

async function discoverHPCInfo(): Promise<void> {
  if (!connectionSessionId.value) return;
  discoveringHPC.value = true;
  discoverError.value = null;
  try {
    const fetchUtils = utils as unknown as { FetchUtils: { post(_url: string, _data: unknown): Promise<unknown> } };
    const result = await fetchUtils.FetchUtils.post("/api/ssh/run-info/", {
      session_id: connectionSessionId.value,
    });
    const r = result as { partitions?: Array<Record<string, unknown>> } | null;
    if (r && r.partitions && r.partitions.length > 0) {
      partitions.value = r.partitions.map((p): PartitionRow => ({
        partition: (p.partition as string) || "",
        maxRunTime: (p.maxRunTime as number) || (p.maxWalltimeHours as number) || null,
        nodes: (p.nodes as number) || null,
        maxCpusPerNode: (p.maxCpusPerNode as number) || null,
        maxMemMbPerNode: (p.maxMemMbPerNode as number) || null,
        maxGpusPerNode: (p.maxGpusPerNode as number) || null,
        gpuTypesStr: Array.isArray(p.gpuTypes) ? (p.gpuTypes as string[]).join(", ") : "",
        accountsStr: Array.isArray(p.accounts) ? (p.accounts as string[]).join(", ") : "",
      }));
    } else {
      discoverError.value = "No partition data returned from HPC discovery.";
    }
  } catch (e) {
    const err = e as { message?: string };
    discoverError.value = err?.message || "Failed to discover HPC info.";
  }
  discoveringHPC.value = false;
}

async function saveResource(): Promise<void> {
  saving.value = true;
  saveError.value = null;
  saveSuccess.value = false;
  try {
    const batch_queues = partitions.value
      .filter((p) => p.partition && p.partition.trim())
      .map((p) => ({
        queue_name: p.partition.trim(),
        max_run_time: p.maxRunTime || undefined,
        max_nodes: p.nodes || undefined,
        cpu_per_node: p.maxCpusPerNode || undefined,
        max_memory: p.maxMemMbPerNode || undefined,
      }));

    const payload = {
      ...(resource.value as Record<string, unknown>),
      batch_queues,
    };

    await services.ComputeResourceService.update({
      lookup: props.computeResourceId,
      data: payload,
    });

    if (jobSubmission.resourceManagerType) {
      await saveSshSubmission();
    }

    saveSuccess.value = true;
    // Reload to reflect server state
    await loadResource();
  } catch (e) {
    const err = e as { message?: string };
    saveError.value = err?.message || "Failed to save compute resource.";
  }
  saving.value = false;
}

async function saveSshSubmission(): Promise<void> {
  const ssh_job_submission: Record<string, unknown> = {
    security_protocol: jobSubmission.securityProtocol || "SSH_KEYS",
    ssh_port: jobSubmission.sshPort || 22,
    monitor_mode: jobSubmission.monitorMode || "POLL_JOB_MANAGER",
    alternative_ssh_host_name: jobSubmission.alternativeSshHostname || "",
    resource_job_manager: {
      resource_job_manager_type: jobSubmission.resourceManagerType,
      job_manager_bin_path: jobSubmission.jobManagerBinPath || "",
    },
  };

  if (jobSubmission.submissionInterfaceId) {
    ssh_job_submission.job_submission_interface_id = jobSubmission.submissionInterfaceId;
    await services.ComputeResourceService.updateSshSubmission({
      lookup: props.computeResourceId,
      data: {
        submission_id: jobSubmission.submissionInterfaceId,
        ssh_job_submission,
      },
    });
  } else {
    await services.ComputeResourceService.addSshSubmission({
      lookup: props.computeResourceId,
      data: {
        priority: 0,
        ssh_job_submission,
      },
    });
  }
}

async function deleteResource(): Promise<void> {
  const res = resource.value as Record<string, unknown>;
  if (
    !window.confirm(
      `Delete compute resource "${res.host_name}"? This action cannot be undone.`,
    )
  ) {
    return;
  }
  try {
    await services.ComputeResourceService.delete({
      lookup: props.computeResourceId,
    });
    window.location.href = "/resources/compute";
  } catch (e) {
    const err = e as { message?: string };
    window.alert(err?.message || "Failed to delete compute resource.");
  }
}

onMounted(() => {
  loadResource();
});

onBeforeUnmount(() => {
  if (sseHandler) {
    getSseClient()?.off("ssh_result", sseHandler);
  }
});
</script>
