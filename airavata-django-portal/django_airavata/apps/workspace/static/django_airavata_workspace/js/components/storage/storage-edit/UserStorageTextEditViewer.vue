<template>
  <div>
    <div class="user-storage-file-edit-viewer-status">
      <div class="user-storage-file-edit-viewer-status-message">
        <span v-if="editAvailable && !readOnly && saved"
          >All the changes are saved.</span
        >
        <span v-if="editAvailable && !readOnly && !saved"
          >Changes are not saved.</span
        >
      </div>
      <div class="user-storage-file-edit-viewer-status-actions">
        <user-storage-download-button
          :data-product-uri="dataProductUri"
          :file-name="fileName"
        />
        <Button
          variant="outline"
          v-if="editAvailable && !readOnly"
          :disabled="saved"
          @click="fileContentChanged"
          >Save</Button
        >
      </div>
    </div>
    <div style="width: 100%" ref="editor" v-if="editAvailable"></div>
    <div class="user-storage-file-edit-viewer-no-preview" v-else>
      Inline edit not available. Click the <strong>Download</strong> button to
      download the file.
    </div>
  </div>
</template>

<script>
import { EditorState } from "@codemirror/state";
import { abcdef } from "@uiw/codemirror-theme-abcdef";
import { EditorView, basicSetup } from "codemirror";
import { services, utils } from "django-airavata-api";
import UserStorageDownloadButton from "./UserStorageDownloadButton";

const MAX_EDIT_FILESIZE = 1024 * 1024;

export default {
  name: "user-storage-file-edit-viewer",
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
  components: {
    UserStorageDownloadButton: UserStorageDownloadButton,
  },
  data() {
    return {
      fileContent: "",
      saved: true,
      editor: null,
      dataProduct: null,
    };
  },
  mounted() {
    this.setFileContent();
  },
  unmounted() {
    // this.editor is created only when the file is small enough to be
    // previewed/edited in browser
    if (this.editor) {
      this.editor.destroy();
    }
  },
  computed: {
    editAvailable() {
      return (
        !this.dataProduct || this.dataProduct.product_size < MAX_EDIT_FILESIZE
      );
    },
    userHasWriteAccess() {
      return this.dataProduct && this.dataProduct.user_has_write_access;
    },
    readOnly() {
      return !this.userHasWriteAccess;
    },
  },
  methods: {
    fileContentChanged() {
      const changedFileContent = this.editor.state.doc.toString();
      if (changedFileContent) {
        utils.FetchUtils.put(
          `/api/data-products?product-uri=${this.dataProductUri}`,
          {
            fileContentText: changedFileContent,
          },
        ).then(() => {
          this.$emit("file-content-changed", changedFileContent);
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
            this.fileContent = res;
            this.setFileContentEditor(this.fileContent);
          });
        }
      });
    },
    setFileContentEditor(value = "") {
      // CodeMirror 6: basicSetup brings line numbers, history, and the default
      // keymap (incl. Ctrl-Space autocomplete); lineWrapping + the abcdef theme
      // and readOnly facet mirror the previous CM5 options.
      this.editor = new EditorView({
        parent: this.$refs.editor,
        state: EditorState.create({
          doc: value,
          extensions: [
            basicSetup,
            EditorView.lineWrapping,
            abcdef,
            EditorState.readOnly.of(this.readOnly),
            EditorView.updateListener.of((update) => {
              if (update.docChanged) {
                this.saved = false;
              }
            }),
          ],
        }),
      });
    },
  },
};
</script>

<style>
.cm-editor {
  height: auto;
  min-height: 600px;
}
</style>
