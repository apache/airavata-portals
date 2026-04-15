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
            {{ resource.host_name }}
            <span class="badge bg-success ms-2" v-if="resource.enabled" style="font-size:0.7rem;vertical-align:middle;">Enabled</span>
            <span class="badge bg-secondary ms-2" v-else style="font-size:0.7rem;vertical-align:middle;">Disabled</span>
          </h1>
          <p class="text-muted mb-0" style="font-size:0.8125rem;" v-if="resource.resource_description">{{ resource.resource_description }}</p>
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
              <input type="text" class="form-control form-control-sm" v-model="resource.host_name" />
            </div>
            <div class="col-md-6">
              <label class="form-label form-label-sm">Description</label>
              <input type="text" class="form-control form-control-sm" v-model="resource.resource_description" placeholder="Optional" />
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
              <input type="number" class="form-control form-control-sm" v-model.number="resource.cpus_per_node" min="1" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Max Memory (MB)</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.max_memory_per_node" min="0" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default Node Count</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.default_node_count" min="1" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default CPU Count</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.default_cpu_count" min="1" />
            </div>
            <div class="col-md-2">
              <label class="form-label form-label-sm">Default Walltime (min)</label>
              <input type="number" class="form-control form-control-sm" v-model.number="resource.default_walltime" min="1" />
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
                  <td><input type="text" class="form-control form-control-sm" v-model="p.partition" placeholder="e.g. debug" /></td>
                  <td><input type="number" class="form-control form-control-sm" v-model.number="p.maxRunTime" min="1" style="width:90px;" placeholder="hours" /></td>
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

      <!-- Card 4: SSH Job Submission -->
      <div class="card mb-3">
        <div class="card-header" style="font-size:0.875rem;font-weight:600;">SSH Job Submission</div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label form-label-sm">Resource Manager</label>
              <select class="form-select form-select-sm" v-model="jobSubmission.resourceManagerType">
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
              <input type="text" class="form-control form-control-sm" v-model="jobSubmission.jobManagerBinPath" placeholder="/usr/bin" />
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">SSH Port</label>
              <input type="number" class="form-control form-control-sm" v-model.number="jobSubmission.sshPort" min="1" max="65535" placeholder="22" />
            </div>
            <div class="col-md-4">
              <label class="form-label form-label-sm">Security Protocol</label>
              <select class="form-select form-select-sm" v-model="jobSubmission.securityProtocol">
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
              <select class="form-select form-select-sm" v-model="jobSubmission.monitorMode">
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
              <input type="text" class="form-control form-control-sm" v-model="jobSubmission.alternativeSshHostname" placeholder="Optional" />
            </div>
          </div>
          <div class="form-text mt-2" style="font-size:0.75rem;">
            SSH submission is saved separately from the general compute resource details.
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
        // Backing state for the SSH job submission + its embedded
        // ResourceJobManager. These fields are persisted via a separate
        // endpoint from the main compute resource PUT.
        submissionInterfaceId: null,
        resourceManagerType: "",
        jobManagerBinPath: "",
        sshPort: 22,
        alternativeSshHostname: "",
        securityProtocol: "SSH_KEYS",
        monitorMode: "POLL_JOB_MANAGER",
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
        // Find the first SSH-protocol submission interface, if any.
        let sshInterfaceId = null;
        if (
          this.resource.job_submission_interfaces &&
          this.resource.job_submission_interfaces.length > 0
        ) {
          const sshIface = this.resource.job_submission_interfaces.find(
            (i) =>
              i.job_submission_protocol === "SSH" ||
              i.job_submission_protocol === "SSH_FORK"
          );
          if (sshIface) {
            sshInterfaceId = sshIface.job_submission_interface_id;
          }
        }
        // Load the SSH submission detail (separate endpoint).
        if (sshInterfaceId) {
          try {
            const sshDetail = await utils.FetchUtils.get(
              "/api/job/submission/ssh",
              { id: sshInterfaceId }
            );
            if (sshDetail) {
              this.jobSubmission.submissionInterfaceId = sshInterfaceId;
              this.jobSubmission.sshPort = sshDetail.ssh_port || 22;
              this.jobSubmission.alternativeSshHostname =
                sshDetail.alternative_ssh_host_name || "";
              this.jobSubmission.securityProtocol =
                sshDetail.security_protocol || "SSH_KEYS";
              this.jobSubmission.monitorMode =
                sshDetail.monitor_mode || "POLL_JOB_MANAGER";
              const rjm = sshDetail.resource_job_manager || {};
              this.jobSubmission.resourceManagerType =
                rjm.resource_job_manager_type || "";
              this.jobSubmission.jobManagerBinPath =
                rjm.job_manager_bin_path || "";
            }
          } catch (e) {
            // Non-fatal: form stays at defaults.
            // eslint-disable-next-line no-console
            console.warn("Failed to load SSH submission details", e);
          }
        }
        // Load existing batch queues as partitions.
        if (
          this.resource.batch_queues &&
          this.resource.batch_queues.length > 0
        ) {
          this.partitions = this.resource.batch_queues.map((q) => ({
            partition: q.queue_name || "",
            maxRunTime: q.max_run_time || null,
            nodes: q.max_nodes || null,
            maxCpusPerNode: q.cpu_per_node || null,
            maxMemMbPerNode: q.max_memory || null,
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
        maxRunTime: null,
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
          host: this.resource.host_name,
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
            maxRunTime: p.maxRunTime || p.maxWalltimeHours || null,
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
        // Map partitions back to batch_queues. max_run_time is what the
        // server uses as the walltime cap for SLURM submissions.
        const batch_queues = this.partitions
          .filter((p) => p.partition && p.partition.trim())
          .map((p) => ({
            queue_name: p.partition.trim(),
            max_run_time: p.maxRunTime || undefined,
            max_nodes: p.nodes || undefined,
            cpu_per_node: p.maxCpusPerNode || undefined,
            max_memory: p.maxMemMbPerNode || undefined,
          }));

        const payload = {
          ...this.resource,
          batch_queues,
        };

        await services.ComputeResourceService.update({
          lookup: this.computeResourceId,
          data: payload,
        });

        // Save the SSH submission separately, if the user has selected
        // a resource manager type. The SSH submission is NOT part of the
        // ComputeResourceDescription proto, so it has its own endpoint.
        if (this.jobSubmission.resourceManagerType) {
          await this.saveSshSubmission();
        }

        this.saveSuccess = true;
        // Reload to reflect server state
        await this.loadResource();
      } catch (e) {
        this.saveError = e?.message || "Failed to save compute resource.";
      }
      this.saving = false;
    },

    async saveSshSubmission() {
      const ssh_job_submission = {
        security_protocol: this.jobSubmission.securityProtocol || "SSH_KEYS",
        ssh_port: this.jobSubmission.sshPort || 22,
        monitor_mode:
          this.jobSubmission.monitorMode || "POLL_JOB_MANAGER",
        alternative_ssh_host_name:
          this.jobSubmission.alternativeSshHostname || "",
        resource_job_manager: {
          resource_job_manager_type:
            this.jobSubmission.resourceManagerType,
          job_manager_bin_path:
            this.jobSubmission.jobManagerBinPath || "",
        },
      };

      if (this.jobSubmission.submissionInterfaceId) {
        ssh_job_submission.job_submission_interface_id =
          this.jobSubmission.submissionInterfaceId;
        await services.ComputeResourceService.updateSshSubmission({
          lookup: this.computeResourceId,
          data: {
            submission_id: this.jobSubmission.submissionInterfaceId,
            ssh_job_submission,
          },
        });
      } else {
        await services.ComputeResourceService.addSshSubmission({
          lookup: this.computeResourceId,
          data: {
            priority: 0,
            ssh_job_submission,
          },
        });
      }
    },

    async deleteResource() {
      if (
        !window.confirm(
          `Delete compute resource "${this.resource.host_name}"? This action cannot be undone.`
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
