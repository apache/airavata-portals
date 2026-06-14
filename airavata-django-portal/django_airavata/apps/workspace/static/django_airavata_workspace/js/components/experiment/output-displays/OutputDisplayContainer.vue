<template>
  <Card>
    <CardHeader class="border-b">
      <div class="flex items-baseline">
        <h6 class="font-semibold">{{ experimentOutput.name }}</h6>
        <DropdownMenu v-if="showMenu">
          <DropdownMenuTrigger as-child>
            <Button variant="outline" size="sm" class="ml-auto">
              {{ currentView["name"] }}
              <ChevronDown class="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              v-for="(view, index) in outputViews"
              :key="view['provider-id']"
              :class="{
                'bg-accent': view['provider-id'] === currentView['provider-id'],
              }"
              @click="selectView(index)"
              >{{ view["name"] }}</DropdownMenuItem
            >
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </CardHeader>
    <CardContent>
      <component
        :is="outputDisplayComponentName"
        :view-data="viewData"
        :data-products="dataProducts"
        :experiment-output="experimentOutput"
      />
      <interactive-parameters-panel
        ref="interactiveParametersPanel"
        v-if="viewData && viewData.interactive"
        :parameters="viewData.interactive"
        @input="parametersUpdated"
      />
    </CardContent>
    <CardFooter
      class="border-t"
      v-if="dataProducts.length > 0 || isExecuting"
    >
      <div class="flex w-full items-baseline justify-end">
        <template v-if="isExecuting">
          <span class="mr-2 text-sm text-muted-foreground">
            {{ fetchIntermediateOutputStatusMessage }}</span
          >
          <Button
            variant="outline"
            size="sm"
            @click="fetchLatest"
            :disabled="fetchLatestDisabled"
          >
            <Loader2
              v-if="currentlyRunningIntermediateOutputFetch"
              class="size-4 animate-spin"
            />
            Fetch Latest</Button
          >
        </template>
        <template v-else-if="dataProducts.length === 1">
          <Button
            as="a"
            variant="outline"
            size="sm"
            :href="downloadUrl(dataProducts[0]) + '&download'"
            >Download</Button
          >
        </template>
      </div>
    </CardFooter>
  </Card>
</template>

<script>
import { ChevronDown, Loader2 } from "@lucide/vue";
import { models } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import DefaultOutputDisplay from "./DefaultOutputDisplay";
import HtmlOutputDisplay from "./HtmlOutputDisplay";
import ImageOutputDisplay from "./ImageOutputDisplay";
import LinkOutputDisplay from "./LinkOutputDisplay";
import NotebookOutputDisplay from "./NotebookOutputDisplay";
import InteractiveParametersPanel from "./interactive-parameters/InteractiveParametersPanel";
import OutputViewDataLoader from "./OutputViewDataLoader";
import { mapActions, mapState } from "pinia";
import { useViewExperimentStore } from "../../../store";
import ProcessState from "django-airavata-api/static/django_airavata_api/js/models/ProcessState";

export default {
  name: "output-viewer-container",
  props: {
    experimentOutput: {
      type: models.OutputDataObjectType,
      required: true,
    },
  },
  components: {
    ChevronDown,
    Loader2,
    "data-product-viewer": components.DataProductViewer,
    DefaultOutputDisplay,
    HtmlOutputDisplay,
    ImageOutputDisplay,
    LinkOutputDisplay,
    NotebookOutputDisplay,
    InteractiveParametersPanel,
  },
  created() {
    // Only show the default output view while executing or if no output dataProducts
    if (
      this.outputViews.length > 0 &&
      (!this.isFinished || this.dataProducts.length === 0)
    ) {
      this.currentViewIndex = this.outputViews.findIndex(
        (ov) => ov["provider-id"] === "default",
      );
    }
    if (this.providerId && this.providerId !== "default") {
      this.loader = this.createLoader();
      this.loader.load();
    }
  },
  data() {
    return {
      currentViewIndex: 0,
      loader: null,
    };
  },
  computed: {
    ...mapState(useViewExperimentStore, [
      "fullExperiment",
      "outputDataProducts",
      "experimentId",
      "isExecuting",
      "isJobActive",
      "isFinished",
      "currentlyRunningIntermediateOutputFetches",
      "userHasWriteAccess",
    ]),
    outputViews() {
      return this.fullExperiment
        ? this.fullExperiment.output_views[this.experimentOutput.name]
        : [];
    },
    dataProducts() {
      return this.outputDataProducts[this.experimentOutput.name];
    },
    currentView() {
      return this.outputViews.length > this.currentViewIndex
        ? this.outputViews[this.currentViewIndex]
        : null;
    },
    viewData() {
      return this.loader && this.loader.data
        ? this.loader.data
        : this.outputViewData;
    },
    outputViewData() {
      return this.currentView && this.currentView.data
        ? this.currentView.data
        : {};
    },
    displayTypeData() {
      return {
        default: {
          component: "default-output-display",
          url: null,
        },
        link: {
          component: "link-output-display",
          url: "/api/link-output/",
        },
        notebook: {
          component: "notebook-output-display",
          url: "/api/notebook-output/",
        },
        html: {
          component: "html-output-display",
          url: "/api/html-output/",
        },
        image: {
          component: "image-output-display",
          url: "/api/image-output/",
        },
      };
    },
    displayType() {
      return this.currentView ? this.currentView["display-type"] : null;
    },
    outputDisplayComponentName() {
      if (this.displayType in this.displayTypeData) {
        return this.displayTypeData[this.displayType].component;
      } else {
        return null;
      }
    },
    outputDataURL() {
      if (this.displayType in this.displayTypeData) {
        return this.displayTypeData[this.displayType].url;
      } else {
        return null;
      }
    },
    showMenu() {
      return (
        this.isFinished &&
        this.outputViews.length > 1 &&
        this.dataProducts.length > 0
      );
    },
    providerId() {
      return this.currentView ? this.currentView["provider-id"] : null;
    },
    hasInteractiveParameters() {
      return this.viewData && this.viewData.interactive;
    },
    currentlyRunningIntermediateOutputFetch() {
      return this.currentlyRunningIntermediateOutputFetches[
        this.experimentOutput.name
      ];
    },
    canFetchIntermediateOutput() {
      return this.isJobActive && !this.currentlyRunningIntermediateOutputFetch;
    },
    fetchLatestDisabled() {
      return !this.canFetchIntermediateOutput || !this.userHasWriteAccess;
    },
    fetchIntermediateOutputStatusMessage() {
      let msg = "";
      if (
        this.experimentOutput.intermediate_output &&
        this.experimentOutput.intermediate_output.process_status &&
        this.experimentOutput.intermediate_output.process_status.isFinished
      ) {
        const timestamp =
          this.experimentOutput.intermediate_output.process_status
            .time_of_state_change;
        msg +=
          "Latest output fetched on " +
          timestamp.toLocaleString([], {
            dateStyle: "medium",
            timeStyle: "short",
          }) +
          ". ";
      }
      if (
        this.experimentOutput.intermediate_output &&
        this.experimentOutput.intermediate_output.process_status
      ) {
        if (
          this.experimentOutput.intermediate_output.process_status.state ===
          ProcessState.FAILED
        ) {
          msg += "Last fetch failed, please try again.";
        }
      }
      return msg;
    },
  },
  methods: {
    ...mapActions(useViewExperimentStore, ["submitFetchIntermediateOutputs"]),
    // downloadURL is no longer on the wire; build it from the data product URI.
    downloadUrl(dataProduct) {
      return `/sdk/download/?data-product-uri=${encodeURIComponent(
        dataProduct.product_uri,
      )}`;
    },
    selectView(outputViewIndex) {
      this.currentViewIndex = outputViewIndex;
      if (this.outputDataURL === null) {
        this.loader = null;
      } else {
        this.loader = this.createLoader();
        this.loader.load();
      }
    },
    parametersUpdated(newParams) {
      if (
        this.hasInteractiveParameters &&
        !this.$refs.interactiveParametersPanel.valid
      ) {
        // Don't update if we have invalid interactive parameters
        return;
      }
      this.loader.load(newParams);
    },
    createLoader() {
      return new OutputViewDataLoader({
        url: this.outputDataURL,
        experimentId: this.experimentId,
        experimentOutputName: this.experimentOutput.name,
        providerId: this.providerId,
      });
    },
    fetchLatest() {
      this.submitFetchIntermediateOutputs({
        outputNames: [this.experimentOutput.name],
      });
    },
  },
};
</script>
