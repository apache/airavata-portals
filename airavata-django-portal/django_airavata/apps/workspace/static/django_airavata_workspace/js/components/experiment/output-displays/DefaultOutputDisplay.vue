<template>
  <div>
    <!-- Show the final data products if available, otherwise, display intermediate outputs -->
    <template v-if="dataProducts.length > 0">
      <pre v-if="finalOutputText">
        {{ finalOutputText }}
      </pre>
      <div v-else v-for="dp in dataProducts" :key="dp.product_uri">
        <img
          v-if="dp.isImage && dp.product_uri"
          class="image-preview rounded"
          :src="downloadUrl(dp)"
        />
        <data-product-viewer :data-product="dp" :mime-type="fileMimeType" />
      </div>
    </template>

    <template v-else-if="intermediateOutputDataProduct">
      <pre v-if="intermediateOutputText">
        {{ intermediateOutputText }}
      </pre>
      <data-product-viewer
        v-else
        :data-product="intermediateOutputDataProduct"
        :mime-type="fileMimeType"
      />
    </template>
    <template v-else-if="intermediateOutputMultipleDataProducts">
      <div
        v-for="dp in intermediateOutputMultipleDataProducts"
        :key="dp.product_uri"
      >
        <data-product-viewer :data-product="dp" :mime-type="fileMimeType" />
      </div>
    </template>
    <template v-else-if="!isExecuting && dataProducts.length === 0">
      <div class="d-flex justify-content-center text-secondary">
        There are no files for this application output.
      </div>
    </template>
  </div>
</template>

<script>
import { models, utils } from "django-airavata-api";
import DataProductViewer from "django-airavata-common-ui/js/components/DataProductViewer.vue";
import { mapGetters } from 'vuex';

const MAX_DISPLAY_TEXT_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

export default {
  name: "default-output-viewer",
  props: {
    experimentOutput: {
      type: models.OutputDataObjectType,
      required: true,
    },
    dataProducts: {
      type: Array,
      required: true,
    },
  },
  components: {
    DataProductViewer,
  },
  data() {
    return {
      intermediateOutputText: null,
      finalOutputText: null,
    };
  },
  async created() {
    // Check and load intermediate or final output as text if available and applicable
    this.loadIntermediateOutputText();
    this.loadFinalOutputText();
  },
  computed: {
    ...mapGetters("viewExperiment", ["isExecuting"]),
    fileMimeType() {
      if (this.experimentOutput.fileMetadataMimeType) {
        return this.experimentOutput.fileMetadataMimeType;
      } else if (
        this.experimentOutput.type === models.DataType.STDOUT ||
        this.experimentOutput.type === models.DataType.STDERR
      ) {
        return "text/plain";
      } else {
        return null;
      }
    },
    intermediateOutputProcessStatusState() {
      if (
        this.experimentOutput &&
        this.experimentOutput.intermediate_output &&
        this.experimentOutput.intermediate_output.process_status
      ) {
        return this.experimentOutput.intermediate_output.process_status.state;
      } else {
        return null;
      }
    },
    intermediateOutputDataProduct() {
      if (
        this.experimentOutput &&
        this.experimentOutput.intermediate_output &&
        this.experimentOutput.intermediate_output.data_products &&
        this.experimentOutput.intermediate_output.data_products.length === 1
      ) {
        return this.experimentOutput.intermediate_output.data_products[0];
      } else {
        return null;
      }
    },
    intermediateOutputMultipleDataProducts() {
      if (
        this.experimentOutput &&
        this.experimentOutput.intermediate_output &&
        this.experimentOutput.intermediate_output.data_products &&
        this.experimentOutput.intermediate_output.data_products.length > 1
      ) {
        return this.experimentOutput.intermediate_output.data_products;
      } else {
        return null;
      }
    },
    intermediateOutputFileSize() {
      if (this.intermediateOutputDataProduct) {
        return this.intermediateOutputDataProduct.product_size;
      } else {
        return -1;
      }
    },
    isIntermediateOutputFileDisplayable() {
      return (
        this.intermediateOutputDataProduct &&
        (this.intermediateOutputDataProduct.isText ||
          this.fileMimeType === "text/plain") &&
        this.intermediateOutputDataProduct.product_uri &&
        this.intermediateOutputDataProduct.product_size <
          MAX_DISPLAY_TEXT_FILE_SIZE
      );
    },
    isFinalOutputFileDisplayable() {
      return (
        this.dataProducts &&
        this.dataProducts.length === 1 &&
        (this.dataProducts[0].isText || this.fileMimeType === "text/plain") &&
        this.dataProducts[0].product_uri &&
        this.dataProducts[0].product_size < MAX_DISPLAY_TEXT_FILE_SIZE
      );
    },
  },
  methods: {
    // downloadURL is no longer on the wire; build it from the URI.
    downloadUrl(dataProduct) {
      return `/sdk/download/?data-product-uri=${encodeURIComponent(
        dataProduct.product_uri
      )}`;
    },
    async loadIntermediateOutputText() {
      if (this.isIntermediateOutputFileDisplayable) {
        this.intermediateOutputText = await utils.FetchUtils.get(
          this.downloadUrl(this.intermediateOutputDataProduct),
          "",
          {
            responseType: "text",
          }
        );
      }
    },
    async loadFinalOutputText() {
      if (this.isFinalOutputFileDisplayable) {
        this.finalOutputText = await utils.FetchUtils.get(
          this.downloadUrl(this.dataProducts[0]),
          "",
          {
            responseType: "text",
          }
        );
      }
    },
  },
  watch: {
    intermediateOutputFileSize() {
      this.loadIntermediateOutputText();
    },
    dataProducts(value, oldValue) {
      if ((!oldValue || oldValue.length === 0) && value && value.length > 0) {
        this.loadFinalOutputText();
      }
    },
  },
};
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
  /* background-color: #efefef; */
  background-color: var(--light);
  border-style: solid;
  border-width: 1px;
  border-color: var(--gray);
  border-radius: 3px;
}
</style>
