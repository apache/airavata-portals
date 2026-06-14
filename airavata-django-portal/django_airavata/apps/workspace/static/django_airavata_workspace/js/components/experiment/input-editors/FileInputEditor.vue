<template>
  <div class="file-input-editor">
    <div class="flex items-center" v-if="isDataProductURI && dataProduct">
      <user-storage-link
        class="mr-auto"
        :data-product-uri="dataProduct.product_uri"
        :mime-type="dataProduct.mimeType"
        :file-name="dataProduct.product_name"
      />
      <delete-link
        v-if="!readOnly && dataProduct.isInputFileUpload"
        class="ml-2"
        @delete="deleteDataProduct"
      >
        Are you sure you want to delete input file
        <strong>{{ dataProduct.product_name }}</strong
        >?
      </delete-link>
      <a
        v-else-if="!readOnly"
        href="#"
        @click.prevent="unselect"
        class="ml-2 inline-flex items-center gap-1 text-muted-foreground"
      >
        Unselect
        <X class="size-4" aria-hidden="true" />
      </a>
    </div>
    <input-file-selector
      v-if="!readOnly && (!isDataProductURI || uploading)"
      :selectedDataProductURIs="selectedDataProductURIs"
      @uploadstart="uploadStart"
      @uploadend="uploadEnd"
      @selected="fileSelected"
    />
  </div>
</template>

<script>
import { X } from "@lucide/vue";
import { models, services, utils } from "django-airavata-api";
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";
import { components } from "django-airavata-common-ui";
import InputFileSelector from "./InputFileSelector";
import UserStorageLink from "../../storage/storage-edit/UserStorageLink";

export default {
  name: "file-input-editor",
  mixins: [InputEditorMixin],
  components: {
    X,
    UserStorageLink,
    "delete-link": components.DeleteLink,
    InputFileSelector,
  },
  computed: {
    isDataProductURI() {
      // Just assume that if the value is a string then it's a data product URL
      return (
        this.value &&
        typeof this.value === "string" &&
        this.value.startsWith("airavata-dp://")
      );
    },
    // When used in the MultiFileInputEditor, don't allow selecting the same
    // file more than once. This computed property creates an array of already
    // selected files.
    selectedDataProductURIs() {
      if (
        this.experimentInput.type === models.DataType.URI_COLLECTION &&
        this.experimentInput.value
      ) {
        return this.experimentInput.value.split(",");
      } else {
        return [];
      }
    },
    isViewable() {
      return this.dataProduct.isText;
    },
  },
  data() {
    return {
      dataProduct: null,
      fileContent: null,
      uploading: false,
    };
  },
  created() {
    if (this.isDataProductURI) {
      this.loadDataProduct(this.value);
    }
  },
  methods: {
    loadDataProduct(dataProductURI) {
      services.DataProductService.retrieve({ lookup: dataProductURI })
        .then((dataProduct) => {
          // A data product with no replica is no longer downloadable; force the
          // user to select or upload another file (downloadURL is gone).
          if (
            !dataProduct.replica_locations ||
            dataProduct.replica_locations.length === 0
          ) {
            this.data = null;
            this.valueChanged();
          } else {
            this.dataProduct = dataProduct;
          }
        })
        .catch(() => {
          // If we're unable to load data product, reset data to null
          this.data = null;
          this.valueChanged();
        });
    },
    deleteDataProduct() {
      utils.FetchUtils.delete(
        "/api/delete-file?data-product-uri=" + encodeURIComponent(this.value),
        { ignoreErrors: true },
      )
        .then(() => {
          this.data = null;
          this.valueChanged();
        })
        .catch((err) => {
          // Ignore 404 Not Found errors, file no longer exists so assume was
          // already deleted
          if (err.details.status === 404) {
            this.data = null;
            this.valueChanged();
          } else {
            throw err;
          }
        })
        .catch(utils.FetchUtils.reportError);
    },
    unselect() {
      this.data = null;
      this.valueChanged();
    },
    fileSelected(dataProductURI, dataProduct) {
      this.data = dataProductURI;
      if (!dataProduct) {
        this.loadDataProduct(dataProductURI);
      } else {
        this.dataProduct = dataProduct;
      }
      this.valueChanged();
    },
    uploadStart() {
      this.uploading = true;
      this.$emit("uploadstart");
    },
    uploadEnd() {
      this.uploading = false;
      this.$emit("uploadend");
    },
  },
  watch: {
    value(value, oldValue) {
      if (this.isDataProductURI && value !== oldValue) {
        this.loadDataProduct(value);
      }
    },
  },
};
</script>

<style scoped>
.input-file-option {
  flex: 1 1 50%;
}
</style>
