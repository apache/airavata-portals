<template>
  <div>
    <!-- Show the final data products if available, otherwise, display intermediate outputs -->
    <template v-if="dataProducts.length > 0">
      <pre v-if="finalOutputText">
        {{ finalOutputText }}
      </pre>
      <div v-for="dp in dataProducts" v-else :key="(dp as Record<string, unknown>).productUri as string">
        <img
          v-if="(dp as Record<string, unknown>).isImage && (dp as Record<string, unknown>).download_url"
          class="image-preview rounded"
          :src="(dp as Record<string, unknown>).download_url as string"
        />
        <DataProductViewer :data-product="dp as Record<string, unknown>" :mime-type="fileMimeType ?? undefined" />
      </div>
    </template>

    <template v-else-if="intermediateOutputDataProduct">
      <pre v-if="intermediateOutputText">
        {{ intermediateOutputText }}
      </pre>
      <DataProductViewer
        v-else
        :data-product="intermediateOutputDataProduct as Record<string, unknown>"
        :mime-type="fileMimeType ?? undefined"
      />
    </template>
    <template v-else-if="intermediateOutputMultipleDataProducts">
      <div v-for="dp in intermediateOutputMultipleDataProducts" :key="(dp as Record<string, unknown>).productUri as string">
        <DataProductViewer :data-product="dp as Record<string, unknown>" :mime-type="fileMimeType ?? undefined" />
      </div>
    </template>
    <template v-else-if="!isExecuting && dataProducts.length === 0">
      <div class="d-flex justify-content-center text-secondary">
        There are no files for this application output.
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models, utils } from "django-airavata-api";
import DataProductViewer from "django-airavata-common-ui/js/components/DataProductViewer.vue";
import { useExperimentStore } from "django-airavata-common-ui/js/stores/experiment";

const MAX_DISPLAY_TEXT_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

type OutputDataObjectType = InstanceType<typeof models.OutputDataObjectType>;

const props = defineProps<{
  experimentOutput: OutputDataObjectType;
  dataProducts: unknown[];
}>();

const experimentStore = useExperimentStore();
const isExecuting = computed(() => experimentStore.isExecuting);

const intermediateOutputText = ref<string | null>(null);
const finalOutputText = ref<string | null>(null);

const fileMimeType = computed<string | null>(() => {
  if ((props.experimentOutput as unknown as Record<string, unknown>).fileMetadataMimeType) {
    return (props.experimentOutput as unknown as Record<string, unknown>).fileMetadataMimeType as string;
  } else if (
    props.experimentOutput.type === models.DataType.STDOUT ||
    props.experimentOutput.type === models.DataType.STDERR
  ) {
    return "text/plain";
  } else {
    return null;
  }
});

const intermediateOutput = computed(
  () => (props.experimentOutput as unknown as Record<string, unknown>).intermediateOutput as Record<string, unknown> | undefined,
);

const intermediateOutputDataProduct = computed(() => {
  if (
    intermediateOutput.value &&
    intermediateOutput.value.dataProducts &&
    (intermediateOutput.value.dataProducts as unknown[]).length === 1
  ) {
    return (intermediateOutput.value.dataProducts as unknown[])[0];
  }
  return null;
});

const intermediateOutputMultipleDataProducts = computed(() => {
  if (
    intermediateOutput.value &&
    intermediateOutput.value.dataProducts &&
    (intermediateOutput.value.dataProducts as unknown[]).length > 1
  ) {
    return intermediateOutput.value.dataProducts as unknown[];
  }
  return null;
});

const intermediateOutputFileSize = computed(() => {
  if (intermediateOutputDataProduct.value) {
    return (intermediateOutputDataProduct.value as Record<string, unknown>).filesize as number;
  }
  return -1;
});

const isIntermediateOutputFileDisplayable = computed(() => {
  const dp = intermediateOutputDataProduct.value as Record<string, unknown> | null;
  return (
    dp &&
    (dp.isText || fileMimeType.value === "text/plain") &&
    dp.download_url &&
    (dp.filesize as number) < MAX_DISPLAY_TEXT_FILE_SIZE
  );
});

const isFinalOutputFileDisplayable = computed(() => {
  const dps = props.dataProducts as Record<string, unknown>[];
  return (
    dps &&
    dps.length === 1 &&
    (dps[0].isText || fileMimeType.value === "text/plain") &&
    dps[0].download_url &&
    (dps[0].filesize as number) < MAX_DISPLAY_TEXT_FILE_SIZE
  );
});

async function loadIntermediateOutputText() {
  if (isIntermediateOutputFileDisplayable.value) {
    const dp = intermediateOutputDataProduct.value as Record<string, unknown>;
    intermediateOutputText.value = await utils.FetchUtils.get(
      dp.download_url as string,
      "",
      { responseType: "text" },
    );
  }
}

async function loadFinalOutputText() {
  if (isFinalOutputFileDisplayable.value) {
    const dps = props.dataProducts as Record<string, unknown>[];
    finalOutputText.value = await utils.FetchUtils.get(
      dps[0].download_url as string,
      "",
      { responseType: "text" },
    );
  }
}

watch(intermediateOutputFileSize, () => {
  loadIntermediateOutputText();
});

watch(
  () => props.dataProducts,
  (value, oldValue) => {
    if ((!oldValue || oldValue.length === 0) && value && value.length > 0) {
      loadFinalOutputText();
    }
  },
);

onMounted(() => {
  loadIntermediateOutputText();
  loadFinalOutputText();
});
</script>

<style scoped>
.image-preview {
  display: block;
  max-width: 100%;
  max-height: 120px;
}
pre {
  max-height: 340px;
  overflow: auto;
  max-width: 100%;
  margin-bottom: 0;
  background-color: var(--light);
  border-style: solid;
  border-width: 1px;
  border-color: var(--gray);
  border-radius: 3px;
}
</style>
