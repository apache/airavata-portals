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
        <table v-else class="table table-hover table-sm">
          <thead>
            <tr>
              <th>Name</th>
              <th class="text-nowrap">Type</th>
              <th class="text-nowrap">Owner</th>
              <th class="text-nowrap">Status</th>
              <th class="text-nowrap" style="width: 1%">Actions</th>
            </tr>
          </thead>
          <tbody class="align-middle">
            <tr v-if="computeResources.length === 0">
              <td colspan="5">
                <div class="table-empty">
                  <i class="fa fa-server table-empty__icon"></i>
                  <div class="table-empty__title">No compute resources available</div>
                  <div class="table-empty__text">
                    Register a compute resource using the button above.
                  </div>
                </div>
              </td>
            </tr>
            <tr v-for="resource in computeResources" :key="resource.id" @click="navigateToResource(resource)" style="cursor: pointer">
              <td>
                <i class="fa fa-server me-2 text-muted"></i>
                <strong>{{ resource.name }}</strong>
              </td>
              <td><span class="badge bg-secondary">HPC</span></td>
              <td>
                <span class="fw-medium text-muted">gateway</span>
                <span class="badge bg-primary ms-1">Gateway</span>
              </td>
              <td>
                <span class="badge bg-success" v-if="resource.enabled">Enabled</span>
                <span class="badge bg-secondary" v-else>Disabled</span>
              </td>
              <td class="text-nowrap" style="width: 1%" @click.stop>
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <button type="button" class="btn btn-outline-danger btn-pill" @click="confirmDelete(resource)">
                    <i class="fa fa-trash me-1"></i>Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="computeResources.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ computeResources.length }}</div>
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
        // Use the full list endpoint so the "Enabled" badge reflects the
        // real server-side flag instead of a hardcoded default.
        const resources = await services.ComputeResourceService.list();
        this.computeResources = (resources || []).map((r) => ({
          id: r.compute_resource_id,
          name: r.host_name,
          enabled: !!r.enabled,
        }));
      } catch {
        this.computeResources = [];
      }
      this.loading = false;
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
            host_name: this.newHostName.trim(),
            resource_description: this.newDescription.trim() || undefined,
          },
        });
        Modal.getInstance(this.$refs.registerModal).hide();
        await this.loadComputeResources();
      } catch (e) {
        this.registerError = e?.message || "Failed to register compute resource. Please try again.";
      }
      this.registering = false;
    },
    navigateToResource(resource) {
      window.location.href = '/resources/compute/' + resource.id;
    },
    async confirmDelete(resource) {
      if (!window.confirm(`Delete compute resource "${resource.name}"? This action cannot be undone.`)) {
        return;
      }
      try {
        await services.ComputeResourceService.delete({ lookup: resource.id });
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

