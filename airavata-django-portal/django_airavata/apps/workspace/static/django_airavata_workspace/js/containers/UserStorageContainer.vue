<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Storage</h1>
        <p class="text-muted mb-0">Manage storage resources.</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary btn-sm" @click="showRegisterModal">
          <i class="fa fa-plus me-1"></i>Register New
        </button>
      </div>
    </div>

    <!-- Storage resources list -->
    <div class="card">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center text-muted py-4">
          <i class="fa fa-spinner fa-spin me-1"></i> Loading storage resources...
        </div>
        <table v-else class="table table-hover table-sm mb-0">
          <thead>
            <tr><th>Name</th><th class="text-nowrap" style="width:1%">Actions</th></tr>
          </thead>
          <tbody class="align-middle">
            <tr v-if="storageList.length === 0">
              <td colspan="2">
                <div class="text-center text-muted py-4">
                  <i class="fa fa-hdd mb-2" style="font-size:2rem;"></i>
                  <div><strong>No storage resources configured</strong></div>
                  <div class="small">Contact your administrator to configure a storage resource.</div>
                </div>
              </td>
            </tr>
            <tr v-for="storage in storageList" :key="storage.id">
              <td>
                <a :href="'/resources/storage/' + storage.id + '/'" class="text-decoration-none">
                  <strong>{{ storage.name }}</strong>
                </a>
              </td>
              <td class="text-nowrap">
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <a :href="'/resources/storage/' + storage.id + '/'" class="btn btn-outline-primary btn-pill">
                    <i class="fa fa-cog me-1"></i>Details
                  </a>
                  <a :href="'/resources/storage/' + storage.id + '/tree'" class="btn btn-outline-secondary btn-pill">
                    <i class="fa fa-folder-open me-1"></i>Files
                  </a>
                  <button type="button" class="btn btn-outline-danger btn-pill" @click="confirmDeleteStorage(storage)">
                    <i class="fa fa-trash me-1"></i>Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="storageList.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">
          Showing {{ storageList.length }}
        </div>
      </div>
    </div>

    <!-- Register Modal -->
    <div ref="registerModal" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-sm">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Register Storage Resource</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label">Host Name <span class="text-danger">*</span></label>
              <input class="form-control" v-model="newHostName" placeholder="e.g. storage.example.com" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
            <button class="btn btn-primary btn-sm" @click="registerStorage" :disabled="!newHostName">Register</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from "bootstrap";
import { services } from "django-airavata-api";

export default {
  name: "user-storage-container",
  data() {
    return {
      loading: true,
      storageList: [],
      newHostName: "",
    };
  },
  methods: {
    showRegisterModal() {
      this.newHostName = "";
      new Modal(this.$refs.registerModal).show();
    },
    async registerStorage() {
      try {
        await services.StorageResourceService.create({
          data: { hostName: this.newHostName, storageResourceDescription: "", enabled: true },
        });
        Modal.getInstance(this.$refs.registerModal).hide();
        await this.loadStorageResources();
      } catch (e) {
        console.error("Failed to register storage resource", e);
      }
    },
    async confirmDeleteStorage(storage) {
      if (!confirm('Delete storage resource "' + storage.name + '"? This cannot be undone.')) return;
      try {
        await services.StorageResourceService.delete({ lookup: storage.id });
        await this.loadStorageResources();
      } catch (e) {
        console.error("Failed to delete storage resource", e);
      }
    },
    async loadStorageResources() {
      this.loading = true;
      try {
        const names = await services.StorageResourceService.names();
        this.storageList = Object.entries(names).map(([id, name]) => ({ id, name }));
      } catch {
        this.storageList = [];
      }
      this.loading = false;
    },
  },
  created() {
    this.loadStorageResources();
  },
};
</script>
