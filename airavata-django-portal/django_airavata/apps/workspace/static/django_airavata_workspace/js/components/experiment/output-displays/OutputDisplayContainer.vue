<template>
  <div class="card">
    <div class="card-body">
      <div class="d-flex align-items-baseline">
        <h6>{{ experimentOutput.name }}</h6>
        <div v-if="showMenu" class="dropdown ms-auto" :text="currentView && currentView['name']">
          <a
            v-for="(view, index) in outputViews"
            :key="view['provider-id'] as string"
            class="dropdown-item"
            :active="view['provider-id'] === (currentView && currentView['provider-id'])"
            @click="selectView(index)"
            >{{ view["name"] }}</a
          >
        </div>
      </div>
      <component
        :is="outputDisplayComponentName"
        :view-data="viewData"
        :data-products="dataProducts"
        :experiment-output="experimentOutput"
      />
      <InteractiveParametersPanel
        v-if="viewData && viewData.interactive"
        ref="interactiveParametersPanel"
        :parameters="viewData.interactive as Record<string, unknown>[]"
        @input="parametersUpdated"
      />
      <div
        v-if="dataProducts.length > 0 || isExecuting"
        class="d-flex justify-content-end align-items-baseline"
      >
        <template v-if="isExecuting">
          <span class="small text-muted me-2"> {{ fetchIntermediateOutputStatusMessage }}</span>
          <button class="btn" size="sm" :disabled="fetchLatestDisabled" @click="fetchLatest">
            <div v-if="currentlyRunningIntermediateOutputFetch" class="spinner-border" small></div>
            Fetch Latest
          </button>
        </template>
        <template v-else-if="dataProducts.length === 1">
          <button class="btn" size="sm" :href="(dataProducts[0] as Record<string, unknown>).download_url + '&download'">
            Download
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type Component } from "vue";
import { models } from "django-airavata-api";
import DefaultOutputDisplay from "./DefaultOutputDisplay.vue";
import HtmlOutputDisplay from "./HtmlOutputDisplay.vue";
import ImageOutputDisplay from "./ImageOutputDisplay.vue";
import LinkOutputDisplay from "./LinkOutputDisplay.vue";
import NotebookOutputDisplay from "./NotebookOutputDisplay.vue";
import InteractiveParametersPanel from "./interactive-parameters/InteractiveParametersPanel.vue";
import OutputViewDataLoader from "./OutputViewDataLoader";
import { useExperimentStore } from "django-airavata-common-ui/js/stores/experiment";
import ProcessState from "django-airavata-api/static/django_airavata_api/js/models/ProcessState";

type OutputDataObjectType = InstanceType<typeof models.OutputDataObjectType>;

const props = defineProps<{
  experimentOutput: OutputDataObjectType;
}>();

const experimentStore = useExperimentStore();

const fullExperiment = computed(() => experimentStore.fullExperiment);
const outputDataProducts = computed(() => experimentStore.outputDataProducts);
const experimentId = computed(() => experimentStore.experimentId);
const isExecuting = computed(() => experimentStore.isExecuting);
const isJobActive = computed(() => experimentStore.isJobActive);
const isFinished = computed(() => experimentStore.isFinished);
const currentlyRunningIntermediateOutputFetches = computed(
  () => experimentStore.currentlyRunningIntermediateOutputFetches,
);
const userHasWriteAccess = computed(() => experimentStore.userHasWriteAccess);

const currentViewIndex = ref(0);
const loaderRef = ref<OutputViewDataLoader | null>(null);
const interactiveParametersPanel = ref<{ valid: boolean } | null>(null);

const outputViews = computed<Record<string, unknown>[]>(() =>
  fullExperiment.value
    ? ((fullExperiment.value as Record<string, unknown>).output_views as Record<string, Record<string, unknown>[]>)?.[props.experimentOutput.name] ?? []
    : [],
);

const dataProducts = computed<unknown[]>(() =>
  (outputDataProducts.value as Record<string, unknown[]>)?.[props.experimentOutput.name] ?? [],
);

const currentView = computed<Record<string, unknown> | null>(() =>
  outputViews.value.length > currentViewIndex.value
    ? outputViews.value[currentViewIndex.value]
    : null,
);

const viewData = computed<Record<string, unknown>>(() =>
  loaderRef.value && loaderRef.value.data ? loaderRef.value.data : outputViewData.value,
);

const outputViewData = computed<Record<string, unknown>>(() =>
  currentView.value && currentView.value.data
    ? (currentView.value.data as Record<string, unknown>)
    : {},
);

const displayTypeData: Record<string, { component: Component; url: string | null }> = {
  default: { component: DefaultOutputDisplay, url: null },
  link: { component: LinkOutputDisplay, url: "/api/link-output/" },
  notebook: { component: NotebookOutputDisplay, url: "/api/notebook-output/" },
  html: { component: HtmlOutputDisplay, url: "/api/html-output/" },
  image: { component: ImageOutputDisplay, url: "/api/image-output/" },
};

const displayType = computed<string | null>(() =>
  currentView.value ? (currentView.value["display-type"] as string) : null,
);

const outputDisplayComponentName = computed<Component | null>(() =>
  displayType.value && displayType.value in displayTypeData
    ? displayTypeData[displayType.value].component
    : null,
);

const outputDataURL = computed<string | null>(() =>
  displayType.value && displayType.value in displayTypeData
    ? displayTypeData[displayType.value].url
    : null,
);

const showMenu = computed(
  () => isFinished.value && outputViews.value.length > 1 && dataProducts.value.length > 0,
);

const providerId = computed<string | null>(() =>
  currentView.value ? (currentView.value["provider-id"] as string) : null,
);

const hasInteractiveParameters = computed(
  () => viewData.value && (viewData.value as Record<string, unknown>).interactive,
);

const currentlyRunningIntermediateOutputFetch = computed(
  () => (currentlyRunningIntermediateOutputFetches.value as Record<string, unknown>)?.[props.experimentOutput.name],
);

const canFetchIntermediateOutput = computed(
  () => isJobActive.value && !currentlyRunningIntermediateOutputFetch.value,
);

const fetchLatestDisabled = computed(
  () => !canFetchIntermediateOutput.value || !userHasWriteAccess.value,
);

const fetchIntermediateOutputStatusMessage = computed<string>(() => {
  let msg = "";
  const io = props.experimentOutput as unknown as Record<string, unknown>;
  const intermediateOutput = io.intermediate_output as Record<string, unknown> | undefined;
  const processStatus = intermediateOutput?.process_status as Record<string, unknown> | undefined;
  if (intermediateOutput && processStatus?.isFinished) {
    const timestamp = processStatus.time_of_state_change as Date;
    msg +=
      "Latest output fetched on " +
      timestamp.toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) +
      ". ";
  }
  if (intermediateOutput && processStatus) {
    if (processStatus.state === ProcessState.FAILED) {
      msg += "Last fetch failed, please try again.";
    }
  }
  return msg;
});

onMounted(() => {
  // Only show the default output view while executing or if no output dataProducts
  if (outputViews.value.length > 0 && (!isFinished.value || dataProducts.value.length === 0)) {
    const defaultIdx = outputViews.value.findIndex((ov) => ov["provider-id"] === "default");
    if (defaultIdx >= 0) currentViewIndex.value = defaultIdx;
  }
  if (providerId.value && providerId.value !== "default") {
    loaderRef.value = createLoader();
    loaderRef.value.load();
  }
});

function selectView(outputViewIndex: number) {
  currentViewIndex.value = outputViewIndex;
  if (outputDataURL.value === null) {
    loaderRef.value = null;
  } else {
    loaderRef.value = createLoader();
    loaderRef.value.load();
  }
}

function parametersUpdated(newParams: unknown) {
  if (hasInteractiveParameters.value && interactiveParametersPanel.value && !interactiveParametersPanel.value.valid) {
    return;
  }
  loaderRef.value?.load(newParams as Record<string, unknown>);
}

function createLoader() {
  return new OutputViewDataLoader({
    url: outputDataURL.value,
    experimentId: experimentId.value,
    experimentOutputName: props.experimentOutput.name,
    providerId: providerId.value,
  });
}

function fetchLatest() {
  experimentStore.submitFetchIntermediateOutputs({
    outputNames: [props.experimentOutput.name],
  });
}
</script>
