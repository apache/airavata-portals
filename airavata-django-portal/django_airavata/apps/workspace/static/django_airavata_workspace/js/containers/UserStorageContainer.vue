<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Storage</h1>
        <p class="text-muted mb-0">Browse, upload, and manage your files and directories.</p>
      </div>
      <div class="col-auto" v-if="!activeStorage">
        <button class="btn btn-primary btn-sm" @click="showRegisterModal">
          <i class="fa fa-plus me-1"></i>Register New
        </button>
      </div>
    </div>

    <!-- Level 1: Storage resources list -->
    <div v-if="!activeStorage" class="card">
      <div class="card-body">
        <div v-if="loading" class="text-center py-4 text-muted">
          <i class="fa fa-spinner fa-spin me-1"></i> Loading storage resources...
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
            <tr v-if="storageList.length === 0">
              <td colspan="5">
                <div class="table-empty">
                  <i class="fa fa-hdd table-empty__icon"></i>
                  <div class="table-empty__title">No storage resources configured</div>
                  <div class="table-empty__text">Contact your administrator to configure a storage resource.</div>
                </div>
              </td>
            </tr>
            <tr v-for="storage in storageList" :key="storage.id" @click="openStorage(storage)" style="cursor:pointer;">
              <td>
                <i class="fa fa-database me-2 text-muted"></i>
                <a :href="'/resources/storage/' + storage.id" class="text-decoration-none"><strong>{{ storage.name }}</strong></a>
              </td>
              <td><span class="badge bg-secondary">SFTP</span></td>
              <td>
                <span class="fw-medium text-muted">gateway</span>
                <span class="badge bg-primary ms-1">Gateway</span>
              </td>
              <td><span class="badge bg-success">Connected</span></td>
              <td class="text-nowrap" style="width: 1%">
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <button type="button" class="btn btn-outline-primary btn-pill" @click.stop="openStorage(storage)">
                    <i class="fa fa-folder-open me-1"></i>Browse
                  </button>
                  <button type="button" class="btn btn-outline-danger btn-pill" @click.stop="confirmDeleteStorage(storage)">
                    <i class="fa fa-trash me-1"></i>Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="storageList.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ storageList.length }}</div>
      </div>
    </div>

    <div class="modal fade" ref="registerModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Register Storage Resource</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Host Name <span class="text-danger">*</span></label>
              <input class="form-control" v-model="newHostName" placeholder="e.g. storage.example.com" />
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <input class="form-control" v-model="newDescription" placeholder="Optional description" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
            <button class="btn btn-primary btn-sm" @click="registerStorage" :disabled="!newHostName">Register</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Level 2: File browser for selected storage -->
    <div v-if="activeStorage">
      <div class="mb-2">
        <a href="#" class="text-muted" style="font-size:0.8125rem;" @click.prevent="closeStorage">
          <i class="fa fa-arrow-left me-1"></i>Back to storage list
        </a>
      </div>
      <div class="card">
        <div class="card-body">
          <!-- Toolbar: breadcrumb + upload/add controls -->
          <div class="d-flex align-items-center justify-content-between mb-2">
            <nav aria-label="breadcrumb" class="mb-0">
              <ol class="breadcrumb mb-0" style="font-size:0.8125rem;">
                <li class="breadcrumb-item" style="cursor:pointer;" @click="navigateTo('')">
                  <i class="fa fa-database me-1"></i>{{ activeStorage.name }}
                </li>
                <li v-for="(part, idx) in pathParts" :key="idx"
                  class="breadcrumb-item"
                  :class="{ active: idx === pathParts.length - 1 }"
                  :style="idx < pathParts.length - 1 ? 'cursor:pointer;' : ''"
                  @click="idx < pathParts.length - 1 && navigateTo(pathParts.slice(0, idx + 1).join('/'))"
                >{{ part }}</li>
              </ol>
            </nav>
            <div v-if="userStoragePath && userStoragePath.user_has_write_access" class="d-flex gap-2">
              <div class="input-group input-group-sm" style="max-width:240px;">
                <input class="form-control" v-model="newDirName" placeholder="New directory" @keydown.enter="addDirectory" />
                <button class="btn btn-outline-secondary" @click="addDirectory" :disabled="!newDirName"><i class="fa fa-folder-plus"></i></button>
              </div>
            </div>
          </div>

          <!-- File/dir table -->
          <table class="table table-hover table-sm">
            <thead>
              <tr>
                <th>Name</th>
                <th class="text-nowrap">Size</th>
                <th class="text-nowrap">Last Modified</th>
                <th class="text-nowrap" style="width: 1%">Actions</th>
              </tr>
            </thead>
            <tbody class="align-middle">
              <tr v-if="!userStoragePath">
                <td colspan="4" class="text-center text-muted py-3">
                  <i class="fa fa-spinner fa-spin me-1"></i> Loading...
                </td>
              </tr>
              <tr v-else-if="items.length === 0">
                <td colspan="4">
                  <div class="table-empty">
                    <i class="fa fa-hdd table-empty__icon"></i>
                    <div class="table-empty__title">This directory is empty</div>
                    <div class="table-empty__text">Upload files or create a subdirectory.</div>
                  </div>
                </td>
              </tr>
              <tr v-for="item in items" :key="item.name">
                <td>
                  <a v-if="item.type === 'dir'" href="#" @click.prevent="navigateTo(item.path)">
                    <i class="fa fa-folder me-1 text-warning"></i>{{ item.name }}
                  </a>
                  <span v-else>
                    <i class="fa fa-file me-1 text-muted"></i>{{ item.name }}
                  </span>
                </td>
                <td>{{ formatSize(item.size) }}</td>
                <td class="text-muted text-nowrap">{{ item.modified_time ? formatDate(item.modified_time) : '-' }}</td>
                <td class="text-nowrap" style="width: 1%">
                  <div class="d-flex gap-2 justify-content-end flex-nowrap">
                    <a v-if="item.type === 'dir'" class="btn btn-outline-primary btn-pill"
                      :href="`/sdk/download-dir/?path=${item.path}`"><i class="fa fa-file-archive me-1"></i>Zip</a>
                    <a v-if="item.type === 'file' && item.download_url" class="btn btn-outline-primary btn-pill"
                      :href="`${item.download_url}&download`"><i class="fa fa-download me-1"></i>Download</a>
                    <button v-if="item.user_has_write_access" type="button" class="btn btn-outline-danger btn-pill"
                      @click="deleteItem(item)"><i class="fa fa-trash me-1"></i>Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="items.length > 0 && userStoragePath" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ items.length }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from "bootstrap";
import { services, utils } from "django-airavata-api";

export default {
  name: "user-storage-container",
  data() {
    return {
      loading: true,
      storageList: [],
      activeStorage: null,
      userStoragePath: null,
      currentPath: "",
      newDirName: null,
      newHostName: "",
      newDescription: "",
    };
  },
  computed: {
    pathParts() {
      return this.currentPath ? this.currentPath.split("/").filter(Boolean) : [];
    },
    items() {
      if (!this.userStoragePath || !this.userStoragePath.is_dir) return [];
      const dirs = (this.userStoragePath.directories || [])
        .filter((d) => !d.hidden)
        .map((d) => ({
          name: d.name,
          path: d.path,
          type: "dir",
          size: d.size,
          modifiedTime: d.modified_time,
          userHasWriteAccess: d.user_has_write_access,
        }));
      const files = (this.userStoragePath.files || []).map((f) => ({
        name: f.name,
        path: f.path,
        type: "file",
        size: f.size,
        modifiedTime: f.modified_time,
        downloadURL: f.download_url,
        dataProductURI: f.data_product_uri,
        userHasWriteAccess: f.user_has_write_access,
      }));
      return dirs.concat(files);
    },
  },
  methods: {
    showRegisterModal() {
      this.newHostName = "";
      this.newDescription = "";
      new Modal(this.$refs.registerModal).show();
    },
    async registerStorage() {
      try {
        await services.StorageResourceService.create({
          data: { hostName: this.newHostName, storageResourceDescription: this.newDescription, enabled: true },
        });
        Modal.getInstance(this.$refs.registerModal).hide();
        await this.loadStorageResources();
      } catch (e) {
        console.error("Failed to register storage resource", e);
      }
    },
    async confirmDeleteStorage(storage) {
      if (!confirm("Delete storage resource \"" + storage.name + "\"? This cannot be undone.")) return;
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
    cleanPath(p) {
      return (p || "").replace(/^\/+|\/+$/g, "").replace(/\/\/+/g, "/");
    },
    updateHash() {
      const cp = this.cleanPath(this.currentPath);
      const hash = this.activeStorage
        ? "#/" + encodeURIComponent(this.activeStorage.id) + (cp ? "/" + cp : "")
        : "";
      window.history.replaceState(null, "", window.location.pathname + hash);
    },
    onPopState() {
      const hash = window.location.hash.replace(/^#\/?/, "");
      if (!hash) {
        this.activeStorage = null;
        this.userStoragePath = null;
        this.currentPath = "";
      }
    },
    openStorage(storage) {
      window.location.href = "/resources/storage/" + storage.id + "/";
    },
    closeStorage() {
      this.activeStorage = null;
      this.userStoragePath = null;
      this.currentPath = "";
      this.updateHash();
    },
    navigateTo(path) {
      this.currentPath = this.cleanPath(path);
      this.updateHash();
      const apiPath = this.currentPath ? "~/" + this.currentPath + "/" : "~/";
      this.loadPath(apiPath);
    },
    async loadPath(path) {
      this.userStoragePath = null;
      try {
        const result = await services.UserStoragePathService.get(
          { path },
          { ignoreErrors: true }
        );
        this.userStoragePath = result;
      } catch {
        this.userStoragePath = { isDir: true, directories: [], files: [], parts: [] };
      }
    },
    async addDirectory() {
      if (!this.newDirName) return;
      const dirPath = this.currentPath
        ? "~/" + this.currentPath + "/" + this.newDirName
        : "~/" + this.newDirName;
      await utils.FetchUtils.post("/api/user-storage/" + dirPath);
      this.newDirName = null;
      this.navigateTo(this.currentPath);
    },
    async deleteItem(item) {
      if (!confirm("Delete " + item.name + "?")) return;
      if (item.type === "dir") {
        await utils.FetchUtils.delete("/api/user-storage/~/" + item.path);
      } else if (item.data_product_uri) {
        await utils.FetchUtils.delete("/api/delete-file?data-product-uri=" + encodeURIComponent(item.data_product_uri));
      }
      this.navigateTo(this.currentPath);
    },
    formatSize(size) {
      if (!size && size !== 0) return "-";
      if (size > 1073741824) return Math.round(size / 1073741824) + " GB";
      if (size > 1048576) return Math.round(size / 1048576) + " MB";
      if (size > 1024) return Math.round(size / 1024) + " KB";
      return size + " B";
    },
    formatDate(date) {
      if (!date) return "-";
      try {
        const d = date instanceof Date ? date : new Date(date);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      } catch { return "-"; }
    },
  },
  created() {
    this.loadStorageResources().then(() => {
      // Restore state from URL hash: #/<storageId>/<path>
      const hash = window.location.hash.replace(/^#\/?/, "");
      if (hash) {
        const parts = hash.split("/").filter(Boolean);
        const storageId = decodeURIComponent(parts[0]);
        const path = this.cleanPath(parts.slice(1).join("/"));
        const storage = this.storageList.find((s) => s.id === storageId);
        if (storage) {
          this.activeStorage = storage;
          this.currentPath = path;
          this.loadPath(path ? "~/" + path + "/" : "~/");
        }
      }
    });
    window.addEventListener("popstate", this.onPopState);
  },
  beforeUnmount() {
    window.removeEventListener("popstate", this.onPopState);
  },
};
</script>

