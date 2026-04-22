<template>
  <div>
    <div class="user-storage-file-edit-viewer-status">
      <div class="user-storage-file-edit-viewer-status-message">
        <span v-if="editAvailable && !readOnly && saved">All the changes are saved.</span>
        <span v-if="editAvailable && !readOnly && !saved">Changes are not saved.</span>
      </div>
      <div class="user-storage-file-edit-viewer-status-actions">
        <user-storage-download-button :data-product-uri="dataProductUri" :file-name="fileName" />
        <button
          v-if="editAvailable && !readOnly"
          class="btn"
          :disabled="saved"
          @click="fileContentChanged"
        >
          Save
        </button>
      </div>
    </div>
    <CodeEditor v-if="editAvailable" v-model="currentContent" :line-numbers="true" />
    <div v-else class="user-storage-file-edit-viewer-no-preview">
      Inline edit not available. Click the <strong>Download</strong> button to download the file.
    </div>
  </div>
</template>

<script>
import { services, utils } from "django-airavata-api";
import CodeEditor from "django-airavata-common-ui/js/components/CodeEditor.vue";
import UserStorageDownloadButton from "./UserStorageDownloadButton";

const MAX_EDIT_FILESIZE = 1024 * 1024;

export default {
  name: "UserStorageFileEditViewer",
  components: {
    CodeEditor,
    UserStorageDownloadButton: UserStorageDownloadButton,
  },
  props: {
    fileName: {
      required: true,
    },
    dataProductUri: {
      required: true,
    },
    mimeType: {
      required: true,
    },
    downloadUrl: {
      required: true,
    },
  },
  data() {
    return {
      currentContent: "",
      saved: true,
      dataProduct: null,
      contentLoaded: false,
    };
  },
  computed: {
    editAvailable() {
      return !this.dataProduct || this.dataProduct.filesize < MAX_EDIT_FILESIZE;
    },
    userHasWriteAccess() {
      return this.dataProduct && this.dataProduct.user_has_write_access;
    },
    readOnly() {
      return !this.user_has_write_access;
    },
  },
  watch: {
    currentContent() {
      if (this.contentLoaded) {
        this.saved = false;
      }
    },
  },
  mounted() {
    this.setFileContent();
  },
  methods: {
    fileContentChanged() {
      if (this.currentContent) {
        utils.FetchUtils.put(`/api/data-products?product-uri=${this.dataProductUri}`, {
          fileContentText: this.currentContent,
        }).then(() => {
          this.$emit("file-content-changed", this.currentContent);
        });
      }

      this.saved = true;
    },
    loadDataProduct() {
      return services.DataProductService.retrieve({
        lookup: this.dataProductUri,
      }).then((dataProduct) => {
        this.dataProduct = dataProduct;
        return dataProduct;
      });
    },
    setFileContent() {
      this.loadDataProduct().then(() => {
        if (this.editAvailable) {
          utils.FetchUtils.get(this.downloadUrl, "", {
            ignoreErrors: false,
            showSpinner: true,
            responseType: "text",
          }).then((res) => {
            this.contentLoaded = false;
            this.currentContent = res;
            this.saved = true;
            this.contentLoaded = true;
          });
        }
      });
    },
  },
};
</script>
