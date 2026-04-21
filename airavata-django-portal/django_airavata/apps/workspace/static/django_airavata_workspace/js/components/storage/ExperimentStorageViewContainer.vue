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
        This experiment was archived on {{ experimentArchive.created_date }}.
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

<script>
import { errors, services, utils } from "django-airavata-api";
import ExperimentStoragePathViewer from "./ExperimentStoragePathViewer.vue";

export default {
  name: "ExperimentStorageViewContainer",
  components: {
    ExperimentStoragePathViewer,
  },
  props: {
    experimentId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      experimentStoragePath: null,
      experimentDataDirNotFound: false,
      experimentArchive: null,
    };
  },
  computed: {
    canDownloadDataDirectory() {
      return this.experimentStoragePath && !this.experimentDataDirNotFound;
    },
    archived() {
      return this.experimentArchive?.archived;
    },
    archiveMaxAge() {
      return this.experimentArchive?.max_age;
    },
  },
  created() {
    this.loadExperimentArchive();
    return this.loadExperimentStoragePath("");
  },
  methods: {
    loadExperimentStoragePath(path) {
      return services.ExperimentStoragePathService.get(
        {
          // ExperimentStoragePathService doesn't encode path parameters so must
          // explicitly encode experiment id
          experimentId: encodeURIComponent(this.experimentId),
          path,
        },
        { ignoreErrors: true },
      )
        .then((result) => (this.experimentStoragePath = result))
        .catch((error) => {
          if (errors.ErrorUtils.isAPIException(error) && error.details.status === 404) {
            this.experimentDataDirNotFound = true;
          } else {
            throw error;
          }
        })
        .catch(utils.FetchUtils.reportError);
    },
    directorySelected(path) {
      return this.loadExperimentStoragePath(path);
    },
    async loadExperimentArchive() {
      const experimentArchive = await services.ExperimentArchiveService.get({
        experimentId: this.experimentId,
      });
      this.experimentArchive = experimentArchive;
    },
  },
};
</script>
