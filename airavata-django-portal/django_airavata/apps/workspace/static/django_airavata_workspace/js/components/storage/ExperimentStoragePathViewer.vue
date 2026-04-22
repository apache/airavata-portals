<template>
  <div>
    <storage-path-breadcrumb
      v-if="experimentStoragePath"
      :parts="experimentStoragePath.parts"
      root-name="Exp Data Dir"
      @directory-selected="$emit('directory-selected', $event)"
    />

    <table v-if="experimentStoragePath" class="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Size</th>
          <th>Last Modified</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.name">
          <td>
            <a v-if="item.type === 'dir'" @click="directorySelected(item)">
              <i class="fa fa-folder-open"></i> {{ item.name }}</a
            >
            <a v-else :href="'download_url' in item ? item.download_url : undefined" :target="downloadTarget">
              {{ item.name }}</a
            >
          </td>
          <td>{{ getFormattedSize(item.size) }}</td>
          <td>
            <human-date :date="item.modifiedTime" />
          </td>
          <td>
            <a
              v-if="item.type === 'file' && 'download_url' in item"
              class="action-link"
              :href="`${item.download_url}&download`"
            >
              Download File
              <i class="fa fa-download" aria-hidden="true"></i>
            </a>
            <a
              v-if="item.type === 'dir'"
              class="action-link"
              :href="`/sdk/download-experiment-dir/${encodeURIComponent(experimentId)}/?path=${'path' in item ? item.path : ''}`"
            >
              Download Zip
              <i class="fa fa-file-archive" aria-hidden="true"></i>
            </a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup lang="ts">
import { computed } from "vue";
import StoragePathBreadcrumb from "./StoragePathBreadcrumb.vue";
import { components } from "django-airavata-common-ui";

const HumanDate = components.HumanDate;

interface StorageDirectory {
  name: string;
  path: string;
  hidden?: boolean;
  modified_time: Date;
  size: number;
}

interface StorageFile {
  name: string;
  mime_type?: string;
  data_product_uri?: string;
  download_url?: string;
  modified_time: Date;
  size: number;
}

interface ExperimentStoragePath {
  parts: string[];
  directories: StorageDirectory[];
  files: StorageFile[];
}

const props = withDefaults(
  defineProps<{
    experimentStoragePath: ExperimentStoragePath | null;
    downloadInNewWindow?: boolean;
    experimentId: string;
  }>(),
  {
    downloadInNewWindow: false,
  },
);

const emit = defineEmits<{
  "directory-selected": [path: string];
}>();

const downloadTarget = computed(() => (props.downloadInNewWindow ? "_blank" : "_self"));

const items = computed(() => {
  if (!props.experimentStoragePath) return [];
  const dirs = props.experimentStoragePath.directories
    .filter((d) => !d.hidden)
    .map((d) => ({
      name: d.name,
      path: d.path,
      type: "dir" as const,
      modifiedTime: d.modified_time,
      modifiedTimestamp: d.modified_time.getTime(),
      size: d.size,
    }));
  const files = props.experimentStoragePath.files.map((f) => ({
    name: f.name,
    mimeType: f.mime_type,
    type: "file" as const,
    dataProductURI: f.data_product_uri,
    download_url: f.download_url,
    modifiedTime: f.modified_time,
    modifiedTimestamp: f.modified_time.getTime(),
    size: f.size,
  }));
  return [...dirs, ...files];
});

function getFormattedSize(size: number): string {
  if (size > Math.pow(2, 30)) {
    return Math.round(size / Math.pow(2, 30)) + " GB";
  } else if (size > Math.pow(2, 20)) {
    return Math.round(size / Math.pow(2, 20)) + " MB";
  } else if (size > Math.pow(2, 10)) {
    return Math.round(size / Math.pow(2, 10)) + " KB";
  } else {
    return size + " bytes";
  }
}

function directorySelected(item: { path: string }) {
  emit("directory-selected", item.path);
}
</script>
