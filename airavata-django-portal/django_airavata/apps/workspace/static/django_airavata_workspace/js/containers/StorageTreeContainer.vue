<template>
  <div>
    <div class="mb-2">
      <a :href="'/resources/storage/' + storageResourceId + '/'" class="text-muted" style="font-size:0.8125rem;">
        <i class="fa fa-arrow-left me-1"></i>Back to storage details
      </a>
    </div>

    <div class="card">
      <div class="card-body">
        <!-- Breadcrumb navigation -->
        <div class="d-flex align-items-center justify-content-between mb-2">
          <nav aria-label="breadcrumb" class="mb-0">
            <ol class="breadcrumb mb-0" style="font-size:0.8125rem;">
              <li class="breadcrumb-item" style="cursor:pointer;" @click="navigateTo('')">
                <i class="fa fa-database me-1"></i>Root
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
            <tr v-if="loading">
              <td colspan="4" class="text-center text-muted py-3">
                <i class="fa fa-spinner fa-spin me-1"></i> Loading...
              </td>
            </tr>
            <tr v-else-if="items.length === 0">
              <td colspan="4">
                <div class="text-center text-muted py-4">
                  <i class="fa fa-hdd mb-2" style="font-size:2rem;"></i>
                  <div><strong>This directory is empty</strong></div>
                  <div class="small">Upload files or create a subdirectory.</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in items" :key="item.name">
              <td>
                <a v-if="item.type === 'dir'" :href="treeUrl(item.path)" @click.prevent="navigateTo(item.path)">
                  <i class="fa fa-folder me-1 text-warning"></i>{{ item.name }}
                </a>
                <span v-else>
                  <i class="fa fa-file me-1 text-muted"></i>{{ item.name }}
                </span>
              </td>
              <td>{{ formatSize(item.size) }}</td>
              <td class="text-muted text-nowrap">{{ item.modifiedTime ? formatDate(item.modifiedTime) : '-' }}</td>
              <td class="text-nowrap" style="width: 1%">
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <a v-if="item.type === 'dir'" class="btn btn-outline-primary btn-pill"
                    :href="`/sdk/download-dir/?path=${item.path}`"><i class="fa fa-file-archive me-1"></i>Zip</a>
                  <a v-if="item.type === 'file' && item.downloadURL" class="btn btn-outline-primary btn-pill"
                    :href="`${item.downloadURL}&download`"><i class="fa fa-download me-1"></i>Download</a>
                  <button v-if="item.userHasWriteAccess" type="button" class="btn btn-outline-danger btn-pill"
                    @click="deleteItem(item)"><i class="fa fa-trash me-1"></i>Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="items.length > 0 && !loading" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">
          Showing {{ items.length }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";

export default {
  name: "storage-tree-container",
  props: {
    storageResourceId: { type: String, required: true },
    initialPath: { type: String, default: "" },
  },
  data() {
    return {
      loading: true,
      currentPath: this.initialPath || "",
      userStoragePath: null,
      newDirName: null,
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
          path: this.cleanPath(d.path || (this.currentPath + "/" + d.name)),
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
    cleanPath(p) {
      return (p || "").replace(/^\/+|\/+$/g, "").replace(/\/\/+/g, "/");
    },
    treeUrl(path) {
      const clean = this.cleanPath(path);
      return "/resources/storage/" + this.storageResourceId + "/tree" + (clean ? "/" + clean : "");
    },
    navigateTo(path) {
      this.currentPath = this.cleanPath(path);
      // Update browser URL without reload
      window.history.pushState(null, "", this.treeUrl(this.currentPath));
      this.loadPath();
    },
    async loadPath() {
      this.loading = true;
      this.userStoragePath = null;
      try {
        const apiPath = this.currentPath ? "~/" + this.currentPath + "/" : "~/";
        const result = await services.UserStoragePathService.get(
          { path: apiPath },
          { ignoreErrors: true }
        );
        this.userStoragePath = result;
      } catch {
        this.userStoragePath = { is_dir: true, directories: [], files: [] };
      }
      this.loading = false;
    },
    async addDirectory() {
      if (!this.newDirName) return;
      try {
        const apiPath = this.currentPath
          ? "~/" + this.currentPath + "/" + this.newDirName
          : "~/" + this.newDirName;
        await services.UserStoragePathService.create({ data: {}, path: apiPath });
        this.newDirName = null;
        await this.loadPath();
      } catch (e) {
        console.error("Failed to create directory", e);
      }
    },
    async deleteItem(item) {
      const label = item.type === "dir" ? "directory" : "file";
      if (!confirm(`Delete ${label} "${item.name}"? This cannot be undone.`)) return;
      try {
        const apiPath = "~/" + item.path;
        await services.UserStoragePathService.delete({ path: apiPath });
        await this.loadPath();
      } catch (e) {
        console.error("Failed to delete " + label, e);
      }
    },
    formatSize(bytes) {
      if (bytes == null) return "-";
      if (bytes < 1024) return bytes + " B";
      if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
      if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + " MB";
      return (bytes / 1073741824).toFixed(2) + " GB";
    },
    formatDate(ts) {
      if (!ts) return "-";
      return new Date(ts).toLocaleString();
    },
    onPopState() {
      // Handle browser back/forward
      const match = window.location.pathname.match(/\/tree(?:\/(.*))?$/);
      this.currentPath = match ? this.cleanPath(match[1] || "") : "";
      this.loadPath();
    },
  },
  created() {
    this.loadPath();
    window.addEventListener("popstate", this.onPopState);
  },
  beforeUnmount() {
    window.removeEventListener("popstate", this.onPopState);
  },
};
</script>
