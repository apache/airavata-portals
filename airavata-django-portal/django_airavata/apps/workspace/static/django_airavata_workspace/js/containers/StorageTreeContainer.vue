<template>
  <div>
    <div class="mb-2">
      <a
        :href="'/resources/storage/' + storageResourceId + '/'"
        class="text-muted"
        style="font-size: 0.8125rem"
      >
        <i class="fa fa-arrow-left me-1"></i>Back to storage details
      </a>
    </div>

    <div class="card">
      <div class="card-body">
        <!-- Breadcrumb navigation -->
        <div class="d-flex align-items-center justify-content-between mb-2">
          <nav aria-label="breadcrumb" class="mb-0">
            <ol class="breadcrumb mb-0" style="font-size: 0.8125rem">
              <li class="breadcrumb-item" style="cursor: pointer" @click="navigateTo('')">
                <i class="fa fa-database me-1"></i>Root
              </li>
              <li
                v-for="(part, idx) in pathParts"
                :key="idx"
                class="breadcrumb-item"
                :class="{ active: idx === pathParts.length - 1 }"
                :style="idx < pathParts.length - 1 ? 'cursor:pointer;' : ''"
                @click="
                  idx < pathParts.length - 1 && navigateTo(pathParts.slice(0, idx + 1).join('/'))
                "
              >
                {{ part }}
              </li>
            </ol>
          </nav>
          <div v-if="userStoragePath && (userStoragePath as Record<string, unknown>).user_has_write_access" class="d-flex gap-2">
            <div class="input-group input-group-sm" style="max-width: 240px">
              <input
                v-model="newDirName"
                class="form-control"
                placeholder="New directory"
                @keydown.enter="addDirectory"
              />
              <button
                class="btn btn-outline-secondary"
                :disabled="!newDirName"
                @click="addDirectory"
              >
                <i class="fa fa-folder-plus"></i>
              </button>
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
                  <i class="fa fa-hdd mb-2" style="font-size: 2rem"></i>
                  <div><strong>This directory is empty</strong></div>
                  <div class="small">Upload files or create a subdirectory.</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in items" :key="item.name">
              <td>
                <a
                  v-if="item.type === 'dir'"
                  :href="treeUrl(item.path)"
                  @click.prevent="navigateTo(item.path)"
                >
                  <i class="fa fa-folder me-1 text-warning"></i>{{ item.name }}
                </a>
                <span v-else> <i class="fa fa-file me-1 text-muted"></i>{{ item.name }} </span>
              </td>
              <td>{{ formatSize(item.size) }}</td>
              <td class="text-muted text-nowrap">
                {{ item.modifiedTime ? formatDate(item.modifiedTime) : "-" }}
              </td>
              <td class="text-nowrap" style="width: 1%">
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <a
                    v-if="item.type === 'dir'"
                    class="btn btn-outline-primary btn-pill"
                    :href="`/sdk/download-dir/?path=${item.path}`"
                    ><i class="fa fa-file-archive me-1"></i>Zip</a
                  >
                  <a
                    v-if="item.type === 'file' && item.downloadURL"
                    class="btn btn-outline-primary btn-pill"
                    :href="`${item.downloadURL}&download`"
                    ><i class="fa fa-download me-1"></i>Download</a
                  >
                  <button
                    v-if="item.userHasWriteAccess"
                    type="button"
                    class="btn btn-outline-danger btn-pill"
                    @click="deleteItem(item)"
                  >
                    <i class="fa fa-trash me-1"></i>Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-if="items.length > 0 && !loading"
          class="text-end text-muted"
          style="font-size: 0.75rem; padding: 6px 8px"
        >
          Showing {{ items.length }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { services } from "django-airavata-api";

interface FileItem {
  name: string;
  path: string;
  type: "dir" | "file";
  size: number | null;
  modifiedTime: unknown;
  downloadURL?: string;
  dataProductURI?: string;
  userHasWriteAccess: boolean;
}

const props = withDefaults(defineProps<{
  storageResourceId: string;
  initialPath?: string;
}>(), {
  initialPath: "",
});

const loading = ref(true);
const currentPath = ref(props.initialPath || "");
const userStoragePath = ref<unknown>(null);
const newDirName = ref<string | null>(null);

const pathParts = computed<string[]>(() =>
  currentPath.value ? currentPath.value.split("/").filter(Boolean) : [],
);

const items = computed<FileItem[]>(() => {
  if (!userStoragePath.value) return [];
  const usp = userStoragePath.value as Record<string, unknown>;
  if (!usp.is_dir) return [];
  const dirs = ((usp.directories as Array<Record<string, unknown>>) || [])
    .filter((d) => !d.hidden)
    .map((d): FileItem => ({
      name: d.name as string,
      path: cleanPath((d.path as string) || currentPath.value + "/" + (d.name as string)),
      type: "dir",
      size: d.size as number | null,
      modifiedTime: d.modified_time,
      userHasWriteAccess: d.user_has_write_access as boolean,
    }));
  const files = ((usp.files as Array<Record<string, unknown>>) || []).map((f): FileItem => ({
    name: f.name as string,
    path: f.path as string,
    type: "file",
    size: f.size as number | null,
    modifiedTime: f.modified_time,
    downloadURL: f.download_url as string | undefined,
    dataProductURI: f.data_product_uri as string | undefined,
    userHasWriteAccess: f.user_has_write_access as boolean,
  }));
  return dirs.concat(files);
});

function cleanPath(p: string): string {
  return (p || "").replace(/^\/+|\/+$/g, "").replace(/\/\/+/g, "/");
}

function treeUrl(path: string): string {
  const clean = cleanPath(path);
  return "/resources/storage/" + props.storageResourceId + "/tree" + (clean ? "/" + clean : "");
}

function navigateTo(path: string): void {
  currentPath.value = cleanPath(path);
  // Update browser URL without reload
  window.history.pushState(null, "", treeUrl(currentPath.value));
  loadPath();
}

async function loadPath(): Promise<void> {
  loading.value = true;
  userStoragePath.value = null;
  try {
    const apiPath = currentPath.value ? "~/" + currentPath.value + "/" : "~/";
    const result = await services.UserStoragePathService.get(
      { path: apiPath },
      { ignoreErrors: true },
    );
    userStoragePath.value = result;
  } catch {
    userStoragePath.value = { is_dir: true, directories: [], files: [] };
  }
  loading.value = false;
}

async function addDirectory(): Promise<void> {
  if (!newDirName.value) return;
  try {
    const apiPath = currentPath.value
      ? "~/" + currentPath.value + "/" + newDirName.value
      : "~/" + newDirName.value;
    await services.UserStoragePathService.create({ data: {}, path: apiPath });
    newDirName.value = null;
    await loadPath();
  } catch (e) {
    console.error("Failed to create directory", e);
  }
}

async function deleteItem(item: FileItem): Promise<void> {
  const label = item.type === "dir" ? "directory" : "file";
  if (!confirm(`Delete ${label} "${item.name}"? This cannot be undone.`)) return;
  try {
    const apiPath = "~/" + item.path;
    await services.UserStoragePathService.delete({ path: apiPath });
    await loadPath();
  } catch (e) {
    console.error("Failed to delete " + label, e);
  }
}

function formatSize(bytes: number | null): string {
  if (bytes === null || bytes === undefined) return "-";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + " MB";
  return (bytes / 1073741824).toFixed(2) + " GB";
}

function formatDate(ts: unknown): string {
  if (!ts) return "-";
  return new Date(ts as string | number).toLocaleString();
}

function onPopState(): void {
  // Handle browser back/forward
  const match = window.location.pathname.match(/\/tree(?:\/(.*))?$/);
  currentPath.value = match ? cleanPath(match[1] || "") : "";
  loadPath();
}

onMounted(() => {
  loadPath();
  window.addEventListener("popstate", onPopState);
});

onBeforeUnmount(() => {
  window.removeEventListener("popstate", onPopState);
});
</script>
