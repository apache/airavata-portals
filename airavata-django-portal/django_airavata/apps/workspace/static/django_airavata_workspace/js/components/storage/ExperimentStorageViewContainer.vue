<template>
  <Card>
    <CardHeader class="border-b">
      <div class="flex justify-between">
        <h6 class="mb-0 font-semibold">Experiment Data Directory</h6>
        <a
          v-if="canDownloadDataDirectory"
          class="inline-flex items-center gap-1 text-primary"
          :href="`/sdk/download-experiment-dir/${encodeURIComponent(
            experimentId,
          )}/`"
        >
          Download Zip
          <FileArchive class="size-4" aria-hidden="true" />
        </a>
      </div>
    </CardHeader>
    <CardContent>
      <experiment-storage-path-viewer
        v-if="experimentStoragePath"
        :experiment-storage-path="experimentStoragePath"
        :experiment-id="experimentId"
        @directory-selected="directorySelected"
        :download-in-new-window="true"
      ></experiment-storage-path-viewer>

      <Alert
        v-else-if="archived"
        class="border-transparent bg-warning text-warning-foreground"
      >
        <AlertDescription class="text-warning-foreground">
          This experiment was archived on
          {{ experimentArchive.created_date }}.
        </AlertDescription>
      </Alert>
      <Alert
        v-else-if="experimentDataDirNotFound"
        class="border-transparent bg-warning text-warning-foreground"
      >
        <AlertDescription class="text-warning-foreground">
          Experiment Data Directory does not exist in storage.
        </AlertDescription>
      </Alert>

      <!-- <small class="text-muted-foreground" v-if="archiveMaxAge > 0">
        Data is retained for {{ archiveMaxAge }} days before it is removed and
        archived.
      </small> -->
    </CardContent>
  </Card>
</template>

<script>
import { FileArchive } from "@lucide/vue";
import { errors, services, utils } from "django-airavata-api";
import ExperimentStoragePathViewer from "./ExperimentStoragePathViewer.vue";

export default {
  name: "experiment-storage-view-container",
  components: { FileArchive, ExperimentStoragePathViewer },
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
  created() {
    this.loadExperimentArchive();
    return this.loadExperimentStoragePath("");
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
          if (
            errors.ErrorUtils.isAPIException(error) &&
            error.details.status === 404
          ) {
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
