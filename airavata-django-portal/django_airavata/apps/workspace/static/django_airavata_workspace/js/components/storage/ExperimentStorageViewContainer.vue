<template>
  <div class="card">
    <div class="card-header">
      <div class="d-flex justify-content-between">
        <h6 class="mb-0">Experiment Data Directory</h6>
        <a
          v-if="canDownloadDataDirectory"
          :href="`/sdk/download-experiment-dir/${encodeURIComponent(experimentId)}/`"
        >
          Download Zip
          <i class="fa fa-file-archive" aria-hidden="true"></i>
        </a>
      </div>
    </div>
    <div class="card-body">
      <experiment-storage-path-viewer
        v-if="experimentStoragePath"
        :experiment-storage-path="experimentStoragePath"
        :experiment-id="experimentId"
        :download-in-new-window="true"
        @directory-selected="directorySelected"
      ></experiment-storage-path-viewer>

      <div v-else-if="archived" class="alert alert-warning">
        This experiment was archived on {{ experimentArchive?.created_date }}.
      </div>
      <div v-else-if="experimentDataDirNotFound" class="alert alert-warning">
        Experiment Data Directory does not exist in storage.
      </div>

      <!-- <small class="text-muted" v-if="archiveMaxAge > 0">
      Data is retained for {{ archiveMaxAge }} days before it is removed and
      archived.
    </small> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { errors, services, utils } from "django-airavata-api";
import ExperimentStoragePathViewer from "./ExperimentStoragePathViewer.vue";

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

const props = defineProps<{
  experimentId: string;
}>();

const experimentStoragePath = ref<ExperimentStoragePath | null>(null);
const experimentDataDirNotFound = ref(false);
const experimentArchive = ref<{ archived?: boolean; max_age?: number; created_date?: string } | null>(null);

const canDownloadDataDirectory = computed(
  () => experimentStoragePath.value !== null && experimentStoragePath.value !== undefined && !experimentDataDirNotFound.value,
);
const archived = computed(() => experimentArchive.value?.archived);

function loadExperimentStoragePath(path: string) {
  return services.ExperimentStoragePathService.get(
    {
      // ExperimentStoragePathService doesn't encode path parameters so must
      // explicitly encode experiment id
      experimentId: encodeURIComponent(props.experimentId),
      path,
    },
    { ignoreErrors: true },
  )
    .then((result: ExperimentStoragePath) => (experimentStoragePath.value = result))
    .catch((error: unknown) => {
      if (errors.ErrorUtils.isAPIException(error) && (error as { details: { status: number } }).details.status === 404) {
        experimentDataDirNotFound.value = true;
      } else {
        throw error;
      }
    })
    .catch(utils.FetchUtils.reportError);
}

function directorySelected(path: string) {
  return loadExperimentStoragePath(path);
}

async function loadExperimentArchive() {
  const result = await services.ExperimentArchiveService.get({
    experimentId: props.experimentId,
  });
  experimentArchive.value = result;
}

onMounted(() => {
  loadExperimentArchive();
  loadExperimentStoragePath("");
});
</script>
