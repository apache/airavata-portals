<template>
  <div>
    <!-- Back link -->
    <div class="mb-3">
      <a href="/resources/compute" class="text-muted" style="font-size:0.8125rem;">
        <i class="fa fa-arrow-left me-1"></i>Back to Compute Resources
      </a>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <i class="fa fa-spinner fa-spin me-1"></i> Loading compute resource...
    </div>

    <div v-else-if="!resource" class="alert alert-warning">
      Compute resource not found.
    </div>

    <template v-else>
      <!-- Header -->
      <div class="row align-items-center mb-3">
        <div class="col">
          <h1 class="h4 mb-0">
            {{ resource.hostName }}
            <span class="badge bg-success ms-2" v-if="resource.enabled" style="font-size:0.7rem;vertical-align:middle;">Enabled</span>
            <span class="badge bg-secondary ms-2" v-else style="font-size:0.7rem;vertical-align:middle;">Disabled</span>
          </h1>
          <p class="text-muted mb-0" style="font-size:0.8125rem;" v-if="resource.resourceDescription">{{ resource.resourceDescription }}</p>
        </div>
        <div class="col-auto d-flex gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="testConnection" :disabled="testingConnection || !sshCredentialToken">
            <i class="fa fa-plug me-1"></i>
            <span v-if="testingConnection"><i class="fa fa-spinner fa-spin me-1"></i>Testing...</span>
            <span v-else>Test Connection</span>
          </button>
          <button class="btn btn-outline-danger btn-sm" @click="deleteResource">
            <i class="fa fa-trash me-1"></i>Delete
          </button>
        </div>
      </div>

      <!-- Save error / success alerts -->
      <div v-if="saveError" class="alert alert-danger alert-dismissible" style="font-size:0.8125rem;">
        {{ saveError }}
        <button type="button" class="btn-close" @click="saveError = null"></button>
      </div>
      <div v-if="saveSuccess" class="alert alert-success alert-dismissible" style="font-size:0.8125rem;">
        Compute resource saved successfully.
        <button type="button" class="btn-close" @click="saveSuccess = false"></button>
      </div>

      <!-- Card 1: General -->
      <div class="card mb-3">
        <div class="card-header" style="font-size:0.875rem;font-weight:600;">General</div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label form-label-sm">Host Name</label>
              <input type="text" class="form-control form-control-sm" v-model="resource.hostName" />
            </div>
            <div class="col-md-6">
              <label class="form-label form-label-sm">Description</label>
              <input type="text" class="form-control form-control-sm" v-model="resource.resourceDescription" placeholder="Optional" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Enabled</label>
              <div class="form-check form-switch mt-1">
                <input class="form-check-input" type="checkbox" v-model="resource.enabled" id="enabledSwitch" />
                <label class="form-check-label" for="enabledSwitch" style="font-size:0.8125rem;">{{ resource.enabled ? 'Yes' : 'No' }}</label>
              </div>
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">CPUs Per Node</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.cpusPerNode" min="1" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Max Memory (MB)</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.maxMemoryPerNode" min="0" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default Node Count</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.defaultNodeCount" min="1" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default CPU Count</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.defaultCPUCount" min="1" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default Walltime (min)</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.defaultWalltime" min="1" />
            </div>
          </div>
        </div>
      </div>

      <!-- Card 2: Credentials -->
      <div class="card mb-3">
        <div class="card-header" style="font-size:0.875rem;font-weight:600;">Credentials</div>
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
              style="font-size:0.8125rem;"
            >
              <i :class="connectionStatus.success ? 'fa fa-check-circle' : 'fa fa-times-circle'" class="me-1"></i>
              {{ connectionStatus.message }}
            </div>
          </div>

          <!-- Test connection button -->
          <div class="d-flex gap-2 align-items-center">
            <button
              class="btn btn-outline-secondary btn-sm"
              @click="testConnection"
              :disabled="testingConnection || !sshCredentialToken"
            >
              <span v-if="testingConnection"><i class="fa fa-spinner fa-spin me-1"></i>Testing...</span>
              <span v-else><i class="fa fa-plug me-1"></i>Test Connection</span>
            </button>

            <!-- Discover HPC Info button — shown after successful connection -->
            <button
              v-if="connectionStatus && connectionStatus.success"
              class="btn btn-outline-primary btn-sm"
              @click="discoverHPCInfo"
              :disabled="discoveringHPC"
            >
              <span v-if="discoveringHPC"><i class="fa fa-spinner fa-spin me-1"></i>Discovering...</span>
              <span v-else><i class="fa fa-search me-1"></i>Discover HPC Info</span>
            </button>
          </div>

          <div v-if="discoverError" class="alert alert-danger mt-2 py-2" style="font-size:0.8125rem;">
            {{ discoverError }}
          </div>
        </div>
      </div>

      <!-- Card 3: HPC Configuration (partitions) -->
      <div class="card mb-3">
        <div class="card-header d-flex align-items-center justify-content-between" style="font-size:0.875rem;font-weight:600;">
          <span>HPC Configuration</span>
          <button class="btn btn-outline-secondary btn-sm" @click="addPartitionRow">
            <i class="fa fa-plus me-1"></i>Add Partition
          </button>
        </div>
        <div class="card-body p-0">
          <div v-if="partitions.length === 0" class="table-empty p-4 text-center text-muted">
            <i class="fa fa-th-list table-empty__icon" style="font-size:2rem;display:block;margin-bottom:0.5rem;"></i>
            <div class="table-empty__title">No partitions configured</div>
            <div class="table-empty__text" style="font-size:0.8125rem;">
              Use "Add Partition" or "Discover HPC Info" after a successful SSH connection.
            </div>
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm mb-0" style="font-size:0.8125rem;">
              <thead class="table-light">
                <tr>
                  <th>Partition</th>
                  <th>Nodes</th>
                  <th>CPUs</th>
                  <th>Memory (MB)</th>
                  <th>GPUs</th>
                  <th>GPU Types</th>
                  <th>Accounts</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(p, idx) in partitions" :key="idx">
                  <td><input type="text" class="form-control form-control-sm" v-model="p.partition" placeholder="e.g. general" /></td>
                  <td><input type="number" class="form-control form-control-sm" v-model.number="p.nodes" min="1" style="width:80px;" /></td>
                  <td><input type="number" class="form-control form-control-sm" v-model.number="p.maxCpusPerNode" min="1" style="width:80px;" /></td>
                  <td><input type="number" class="form-control form-control-sm" v-model.number="p.maxMemMbPerNode" min="0" style="width:100px;" /></td>
                  <td><input type="number" class="form-control form-control-sm" v-model.number="p.maxGpusPerNode" min="0" style="width:80px;" /></td>
                  <td><input type="text" class="form-control form-control-sm" v-model="p.gpuTypesStr" placeholder="comma-separated" /></td>
                  <td><input type="text" class="form-control form-control-sm" v-model="p.accountsStr" placeholder="comma-separated" /></td>
                  <td>
                    <button class="btn btn-link btn-sm text-danger p-0" @click="removePartitionRow(idx)" title="Remove">
                      <i class="fa fa-times"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Card 4: Job Submission -->
      <div class="card mb-3">
        <div class="card-header" style="font-size:0.875rem;font-weight:600;">Job Submission</div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label form-label-sm">Resource Manager</label>
              <select class="form-select form-select-sm" v-model="jobSubmission.resourceManager">
                <option value="">-- Select --</option>
                <option value="SLURM">SLURM</option>
                <option value="PBS">PBS</option>
                <option value="SGE">SGE</option>
                <option value="FORK">FORK</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">SSH Port</label>
              <input type="number" class="form-control form-control-sm" v-model.number="jobSubmission.sshPort" min="1" max="65535" placeholder="22" />
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">Alternative SSH Host</label>
              <input type="text" class="form-control form-control-sm" v-model="jobSubmission.alternativeSshHostname" placeholder="Optional" />
            </div>
          </div>
        </div>
      </div>

      <!-- Save button -->
      <div class="d-flex justify-content-end mb-4">
        <button class="btn btn-primary btn-sm" @click="saveResource" :disabled="saving">
          <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
          <span v-else><i class="fa fa-save me-1"></i>Save</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import { services, utils } from "django-airavata-api";
import SSHCredentialSelector from "../../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

export default {
  name: "compute-detail-container",
  components: {
    "ssh-credential-selector": SSHCredentialSelector,
  },
  props: {
    computeResourceId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      loading: true,
      resource: null,
      sshCredentialToken: null,
      partitions: [],
      jobSubmission: {
        resourceManager: "",
        sshPort: 22,
        alternativeSshHostname: "",
      },
      saving: false,
      saveError: null,
      saveSuccess: false,
      testingConnection: false,
      connectionStatus: null,
      connectionSessionId: null,
      discoveringHPC: false,
      discoverError: null,
      sseHandler: null,
    };
  },
  methods: {
    async loadResource() {
      if (!this.computeResourceId) {
        this.loading = false;
        return;
      }
      this.loading = true;
      try {
        this.resource = await services.ComputeResourceService.retrieve({
          lookup: this.computeResourceId,
        });
        // Pull job submission info if available
        if (
          this.resource.jobSubmissionInterfaces &&
          this.resource.jobSubmissionInterfaces.length > 0
        ) {
          const iface = this.resource.jobSubmissionInterfaces[0];
          if (iface.jobSubmissionInterfaceId) {
            this.jobSubmission.resourceManager =
              iface.jobSubmissionProtocol || "";
          }
        }
        // Pull SSH job submission info (sshPort, alternativeSshHostname)
        if (
          this.resource.sshJobSubmission
        ) {
          this.jobSubmission.sshPort =
            this.resource.sshJobSubmission.sshPort || 22;
          this.jobSubmission.alternativeSshHostname =
            this.resource.sshJobSubmission.alternativeSshHostname || "";
          this.jobSubmission.resourceManager =
            this.resource.sshJobSubmission.resourceManager || "";
        }
        // Load existing batch queues as partitions
        if (
          this.resource.batchQueues &&
          this.resource.batchQueues.length > 0
        ) {
          this.partitions = this.resource.batchQueues.map((q) => ({
            partition: q.queueName || "",
            nodes: q.maxNodes || null,
            maxCpusPerNode: q.cpuPerNode || null,
            maxMemMbPerNode: q.maxMemory || null,
            maxGpusPerNode: null,
            gpuTypesStr: "",
            accountsStr: "",
          }));
        }
      } catch {
        this.resource = null;
      }
      this.loading = false;
    },

    addPartitionRow() {
      this.partitions.push({
        partition: "",
        nodes: null,
        maxCpusPerNode: null,
        maxMemMbPerNode: null,
        maxGpusPerNode: null,
        gpuTypesStr: "",
        accountsStr: "",
      });
    },

    removePartitionRow(idx) {
      this.partitions.splice(idx, 1);
    },

    async testConnection() {
      if (!this.sshCredentialToken) return;
      this.testingConnection = true;
      this.connectionStatus = null;
      this.connectionSessionId = null;

      // Register SSE listener before posting
      const handler = (event) => {
        this.testingConnection = false;
        this.connectionStatus = {
          success: event.success === true,
          message: event.message || (event.success ? "Connection successful." : "Connection failed."),
        };
        this.connectionSessionId = event.session_id || null;
        utils.SSEClient.off("ssh_result", handler);
        this.sseHandler = null;
      };
      this.sseHandler = handler;
      utils.SSEClient.connect();
      utils.SSEClient.on("ssh_result", handler);

      try {
        await utils.FetchUtils.post("/api/ssh/test/", {
          compute_resource_id: this.computeResourceId,
          credential_token: this.sshCredentialToken,
          host: this.resource.hostName,
          port: this.jobSubmission.sshPort || 22,
        });
      } catch (e) {
        this.testingConnection = false;
        this.connectionStatus = {
          success: false,
          message: e?.message || "Failed to initiate connection test.",
        };
        utils.SSEClient.off("ssh_result", handler);
        this.sseHandler = null;
      }
    },

    async discoverHPCInfo() {
      if (!this.connectionSessionId) return;
      this.discoveringHPC = true;
      this.discoverError = null;
      try {
        const result = await utils.FetchUtils.post("/api/ssh/run-info/", {
          session_id: this.connectionSessionId,
        });
        if (result && result.partitions && result.partitions.length > 0) {
          this.partitions = result.partitions.map((p) => ({
            partition: p.partition || "",
            nodes: p.nodes || null,
            maxCpusPerNode: p.maxCpusPerNode || null,
            maxMemMbPerNode: p.maxMemMbPerNode || null,
            maxGpusPerNode: p.maxGpusPerNode || null,
            gpuTypesStr: Array.isArray(p.gpuTypes) ? p.gpuTypes.join(", ") : "",
            accountsStr: Array.isArray(p.accounts) ? p.accounts.join(", ") : "",
          }));
        } else {
          this.discoverError = "No partition data returned from HPC discovery.";
        }
      } catch (e) {
        this.discoverError = e?.message || "Failed to discover HPC info.";
      }
      this.discoveringHPC = false;
    },

    async saveResource() {
      this.saving = true;
      this.saveError = null;
      this.saveSuccess = false;
      try {
        // Map partitions back to batchQueues
        const batchQueues = this.partitions.map((p) => ({
          queueName: p.partition,
          maxNodes: p.nodes || undefined,
          cpuPerNode: p.maxCpusPerNode || undefined,
          maxMemory: p.maxMemMbPerNode || undefined,
        }));

        const payload = {
          ...this.resource,
          batchQueues,
        };

        await services.ComputeResourceService.update({
          lookup: this.computeResourceId,
          data: payload,
        });
        this.saveSuccess = true;
        // Reload to reflect server state
        await this.loadResource();
      } catch (e) {
        this.saveError = e?.message || "Failed to save compute resource.";
      }
      this.saving = false;
    },

    async deleteResource() {
      if (
        !window.confirm(
          `Delete compute resource "${this.resource.hostName}"? This action cannot be undone.`
        )
      ) {
        return;
      }
      try {
        await services.ComputeResourceService.delete({
          lookup: this.computeResourceId,
        });
        window.location.href = "/resources/compute";
      } catch (e) {
        window.alert(e?.message || "Failed to delete compute resource.");
      }
    },
  },
  created() {
    this.loadResource();
  },
  beforeUnmount() {
    if (this.sseHandler) {
      utils.SSEClient.off("ssh_result", this.sseHandler);
    }
  },
};
</script>
