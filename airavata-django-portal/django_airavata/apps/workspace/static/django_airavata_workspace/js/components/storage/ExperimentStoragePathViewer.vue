<template>
  <div>
    <storage-path-breadcrumb
      v-if="experimentStoragePath"
      :parts="experimentStoragePath.parts"
      rootName="Exp Data Dir"
      @directory-selected="$emit('directory-selected', $event)"
    />

    <Table v-if="experimentStoragePath">
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Last Modified</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="item in sortedItems" :key="item.path || item.name">
          <TableCell>
            <a
              v-if="item.type === 'dir'"
              href="#"
              class="inline-flex items-center gap-1 text-primary"
              @click.prevent="directorySelected(item)"
            >
              <FolderOpen class="size-4" /> {{ item.name }}</a
            >
            <a
              v-else
              class="text-primary"
              :href="item.downloadURL"
              :target="downloadTarget"
            >
              {{ item.name }}</a
            >
          </TableCell>
          <TableCell>{{ getFormattedSize(item.size) }}</TableCell>
          <TableCell>
            <human-date :date="item.modified_time" />
          </TableCell>
          <TableCell>
            <a
              v-if="item.type === 'file'"
              class="inline-flex items-center gap-1 text-primary"
              :href="`${item.downloadURL}&download`"
            >
              Download File
              <Download class="size-4" aria-hidden="true" />
            </a>
            <a
              v-if="item.type === 'dir'"
              class="inline-flex items-center gap-1 text-primary"
              :href="`/sdk/download-experiment-dir/${encodeURIComponent(
                experimentId,
              )}/?path=${item.path}`"
            >
              Download Zip
              <FileArchive class="size-4" aria-hidden="true" />
            </a>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
<script>
import { Download, FileArchive, FolderOpen } from "@lucide/vue";
import StoragePathBreadcrumb from "./StoragePathBreadcrumb.vue";
import { components } from "django-airavata-common-ui";

export default {
  name: "experiment-storage-path-viewer",
  props: {
    experimentStoragePath: {
      required: true,
    },
    downloadInNewWindow: {
      type: Boolean,
      default: false,
    },
    experimentId: {
      required: true,
    },
  },
  components: {
    Download,
    FileArchive,
    FolderOpen,
    "human-date": components.HumanDate,
    StoragePathBreadcrumb,
  },
  computed: {
    items() {
      if (this.experimentStoragePath) {
        const dirs = this.experimentStoragePath.directories.map((d) => {
          return {
            name: d.name,
            path: d.path,
            type: "dir",
            modified_time: d.modified_time,
            modifiedTimestamp: d.modified_time.getTime(), // for sorting
            size: d.size,
          };
        });
        const files = this.experimentStoragePath.files.map((f) => {
          return {
            name: f.name,
            content_type: f.content_type,
            type: "file",
            data_product_uri: f.data_product_uri,
            // downloadURL is no longer on the wire; build it from the URI.
            downloadURL: `/sdk/download/?data-product-uri=${encodeURIComponent(
              f.data_product_uri,
            )}`,
            modified_time: f.modified_time,
            modifiedTimestamp: f.modified_time.getTime(), // for sorting
            size: f.size,
          };
        });
        return dirs.concat(files);
      } else {
        return [];
      }
    },
    sortedItems() {
      // Preserve the b-table default of sorting by name.
      return this.items
        .slice()
        .sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
    },
    downloadTarget() {
      return this.downloadInNewWindow ? "_blank" : "_self";
    },
  },
  methods: {
    getFormattedSize(size) {
      if (size > Math.pow(2, 30)) {
        return Math.round(size / Math.pow(2, 30)) + " GB";
      } else if (size > Math.pow(2, 20)) {
        return Math.round(size / Math.pow(2, 20)) + " MB";
      } else if (size > Math.pow(2, 10)) {
        return Math.round(size / Math.pow(2, 10)) + " KB";
      } else {
        return size + " bytes";
      }
    },
    directorySelected(item) {
      this.$emit("directory-selected", item.path);
    },
  },
};
</script>
