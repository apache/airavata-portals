<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Compute</h1>
        <p class="text-muted mb-0">Manage compute resources for running experiments.</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary btn-sm" @click="showRegisterModal">
          <i class="fa fa-plus me-1"></i>Register New
        </button>
      </div>
    </div>

    <!-- Compute Resources -->
    <div class="card">
      <div class="card-body">
        <div v-if="loading" class="text-center py-4 text-muted">
          <i class="fa fa-spinner fa-spin me-1"></i> Loading compute resources...
        </div>
        <table v-else class="table table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="computeResources.length === 0">
              <td colspan="4">
                <div class="table-empty">
                  <i class="fa fa-server table-empty__icon"></i>
                  <div class="table-empty__title">No compute resources available</div>
                  <div class="table-empty__text">
                    Register a compute resource using the button above.
                  </div>
                </div>
              </td>
            </tr>
            <tr v-for="resource in computeResources" :key="resource.id">
              <td>
                <i class="fa fa-server me-2 text-muted"></i>
                <a :href="'/resources/compute/' + resource.id" class="text-decoration-none"><strong>{{ resource.name }}</strong></a>
              </td>
              <td><span class="badge bg-secondary">HPC</span></td>
              <td>
                <span class="badge bg-success" v-if="resource.enabled">Enabled</span>
                <span class="badge bg-secondary" v-else>Disabled</span>
              </td>
              <td>
                <a href="#" class="action-link me-2" @click.prevent="viewResource(resource)">
                  <i class="fa fa-eye"></i> View
                </a>
                <a href="#" class="action-link text-danger" @click.prevent="confirmDelete(resource)">
                  <i class="fa fa-trash"></i> Delete
                </a>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="computeResources.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ computeResources.length }}</div>
      </div>
    </div>

    <!-- Resource detail panel -->
    <div v-if="selectedResource" class="card mt-3">
      <div class="card-body">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <h2 class="h5 mb-0">{{ selectedResource.name }}</h2>
          <a href="#" class="text-muted" @click.prevent="selectedResource = null" style="font-size:0.8125rem;">
            <i class="fa fa-times"></i> Close
          </a>
        </div>
        <table class="table">
          <tbody>
            <tr>
              <td class="text-muted" style="width:180px;">Host Name</td>
              <td>{{ selectedResourceDetail ? selectedResourceDetail.hostName : '-' }}</td>
            </tr>
            <tr>
              <td class="text-muted">Description</td>
              <td>{{ selectedResourceDetail ? (selectedResourceDetail.resourceDescription || '-') : '-' }}</td>
            </tr>
            <tr>
              <td class="text-muted">Enabled</td>
              <td>{{ selectedResourceDetail ? (selectedResourceDetail.enabled ? 'Yes' : 'No') : '-' }}</td>
            </tr>
            <tr v-if="selectedResourceDetail && selectedResourceDetail.batchQueues && selectedResourceDetail.batchQueues.length > 0">
              <td class="text-muted">Queues</td>
              <td>
                <span v-for="q in selectedResourceDetail.batchQueues" :key="q.queueName" class="badge bg-secondary me-1">
                  {{ q.queueName }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Register modal -->
    <div class="modal fade" id="registerComputeModal" tabindex="-1" aria-labelledby="registerComputeModalLabel" aria-hidden="true" ref="registerModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="registerComputeModalLabel">Register Compute Resource</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="registerError" class="alert alert-danger" style="font-size:0.8125rem;">
              {{ registerError }}
            </div>
            <div class="mb-3">
              <label for="newHostName" class="form-label">
                Host Name <span class="text-danger">*</span>
              </label>
              <input
                id="newHostName"
                type="text"
                class="form-control"
                v-model="newHostName"
                placeholder="e.g. cluster.example.edu"
                :disabled="registering"
              />
              <div class="form-text" style="font-size:0.8125rem;">The fully qualified domain name of the compute resource.</div>
            </div>
            <div class="mb-3">
              <label for="newDescription" class="form-label">Description</label>
              <textarea
                id="newDescription"
                class="form-control"
                v-model="newDescription"
                rows="3"
                placeholder="Optional description"
                :disabled="registering"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal" :disabled="registering">Cancel</button>
            <button type="button" class="btn btn-primary btn-sm" @click="registerResource" :disabled="registering || !newHostName.trim()">
              <span v-if="registering"><i class="fa fa-spinner fa-spin me-1"></i> Registering...</span>
              <span v-else>Register</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { Modal } from "bootstrap";

export default {
  name: "compute-container",
  data() {
    return {
      loading: true,
      computeResources: [],
      selectedResource: null,
      selectedResourceDetail: null,
      newHostName: "",
      newDescription: "",
      registering: false,
      registerError: null,
    };
  },
  methods: {
    async loadComputeResources() {
      this.loading = true;
      try {
        const names = await services.ComputeResourceService.names();
        this.computeResources = Object.entries(names).map(([id, name]) => ({
          id,
          name,
          enabled: true,
        }));
      } catch {
        this.computeResources = [];
      }
      this.loading = false;
    },
    async viewResource(resource) {
      this.selectedResource = resource;
      this.selectedResourceDetail = null;
      try {
        this.selectedResourceDetail = await services.ComputeResourceService.retrieve({ lookup: resource.id });
      } catch {
        this.selectedResourceDetail = null;
      }
    },
    showRegisterModal() {
      this.newHostName = "";
      this.newDescription = "";
      this.registerError = null;
      new Modal(this.$refs.registerModal).show();
    },
    async registerResource() {
      if (!this.newHostName.trim()) {
        return;
      }
      this.registering = true;
      this.registerError = null;
      try {
        await services.ComputeResourceService.create({
          data: {
            hostName: this.newHostName.trim(),
            resourceDescription: this.newDescription.trim() || undefined,
          },
        });
        Modal.getInstance(this.$refs.registerModal).hide();
        await this.loadComputeResources();
      } catch (e) {
        this.registerError = e?.message || "Failed to register compute resource. Please try again.";
      }
      this.registering = false;
    },
    async confirmDelete(resource) {
      if (!window.confirm(`Delete compute resource "${resource.name}"? This action cannot be undone.`)) {
        return;
      }
      try {
        await services.ComputeResourceService.delete({ lookup: resource.id });
        if (this.selectedResource && this.selectedResource.id === resource.id) {
          this.selectedResource = null;
          this.selectedResourceDetail = null;
        }
        await this.loadComputeResources();
      } catch (e) {
        window.alert(e?.message || "Failed to delete compute resource.");
      }
    },
  },
  created() {
    this.loadComputeResources();
  },
};
</script>
