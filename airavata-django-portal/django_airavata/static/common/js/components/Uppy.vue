<template>
  <div class="custom-Uppy">
    <div ref="dragDrop" />
    <div ref="statusBar" />
    <div v-if="restrictionFailed" class="alert alert-danger mt-1">
      {{ restrictionFailedMessage }}
    </div>
  </div>
</template>

<script>
/* eslint-disable vue/multi-word-component-names */
import { services, utils } from "django-airavata-api";

import Uppy from "@uppy/core";
import DragDrop from "@uppy/drag-drop";
import StatusBar from "@uppy/status-bar";
import Tus from "@uppy/tus";
import XHRUpload from "@uppy/xhr-upload";

import "@uppy/core/dist/style.min.css";
import "@uppy/status-bar/dist/style.min.css";
import "@uppy/drag-drop/dist/style.min.css";

export default {
  name: "Uppy",
  props: {
    xhrUploadEndpoint: {
      type: String,
      required: true,
    },
    // endpoint should accept POST request. Request will include form data with
    // the key uploadURL.
    tusUploadFinishEndpoint: {
      type: String,
      required: false,
    },
    multiple: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      uppy: null,
      restrictionFailedMessage: null,
      settings: null,
      uploadFilesCount: 0,
    };
  },
  computed: {
    maxFileUploadSizeMB() {
      return this.settings ? this.settings.fileUploadMaxFileSize / 1024 / 1024 : 0;
    },
    maxFileUploadSizeMessage() {
      if (this.maxFileUploadSizeMB) {
        return "Max file upload size is " + Math.round(this.maxFileUploadSizeMB) + " MB";
      } else {
        return null;
      }
    },
    restrictionFailed() {
      // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
      return this.restrictionFailedMessage != null;
    },
  },
  watch: {
    xhrUploadEndpoint(val) {
      // Update the xhrUploadEndpoint configuration on XHRUpload whenever it changes
      if (this.uppy && this.settings && !this.settings.tusEndpoint) {
        this.uppy.getPlugin("XHRUpload").setOptions({
          endpoint: val,
        });
      }
    },
  },
  mounted() {
    services.SettingsService.get().then((s) => {
      this.settings = s;
      this.initUppy();
    });
  },
  unmounted() {
    if (this.uppy) {
      this.uppy.close();
    }
  },
  methods: {
    initUppy() {
      this.uppy = Uppy({
        autoProceed: true,
        debug: true,
        restrictions: {
          maxNumberOfFiles: this.multiple ? null : 1,
          maxFileSize: this.settings.fileUploadMaxFileSize,
        },
      });
      this.uppy.use(DragDrop, {
        target: this.$refs.dragDrop,
        note: this.maxFileUploadSizeMessage,
      });
      this.uppy.use(StatusBar, {
        target: this.$refs.statusBar,
        hideUploadButton: true,
        hideAfterFinish: false,
      });
      if (this.settings.tusEndpoint) {
        this.uppy.use(Tus, { endpoint: this.settings.tusEndpoint });
        this.uppy.on("upload-success", (file, response) => {
          const data = new FormData();
          data.append("uploadURL", response.uploadURL);
          utils.FetchUtils.post(this.tusUploadFinishEndpoint, data, "", {
            showSpinner: false,
          }).then((result) => {
            this.$emit("upload-success", result);
            this.fileFinishedUploading();
          });
        });
      } else {
        this.uppy.use(XHRUpload, {
          endpoint: this.xhrUploadEndpoint,
          withCredentials: true,
          headers: {
            "X-CSRFToken": utils.FetchUtils.getCSRFToken(),
          },
          fieldName: "file",
        });
        this.uppy.on("upload-success", (file, response) => {
          this.$emit("upload-success", response.body);
          this.fileFinishedUploading();
        });
      }
      this.uppy.on("upload", (data) => {
        this.$emit("upload-started");
        this.uploadFilesCount = data.fileIDs.length;
      });
      this.uppy.on("complete", () => {
        this.restrictionFailedMessage = null;
      });
      this.uppy.on("restriction-failed", (file, error) => {
        this.restrictionFailedMessage = `${file.name}: ${error.message}`;
      });
      this.uppy.on("upload-error", () => {
        this.fileFinishedUploading();
      });
    },
    fileFinishedUploading() {
      this.uploadFilesCount--;
      if (this.uploadFilesCount <= 0) {
        this.$emit("upload-finished");
      }
    },
    reset() {
      this.uppy.reset();
    },
  },
};
</script>

<style scoped>
.custom-Uppy :deep(.uppy-DragDrop-inner) {
  padding: 5px 0px;
}
.custom-Uppy :deep(.UppyIcon) {
  display: none;
}
.custom-Uppy :deep(.uppy-DragDrop-label) {
  margin-bottom: 0px;
}
.custom-Uppy :deep(.uppy-StatusBar) {
  background-color: inherit;
}
</style>
