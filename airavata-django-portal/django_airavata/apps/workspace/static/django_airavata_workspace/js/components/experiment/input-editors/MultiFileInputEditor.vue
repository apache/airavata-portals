<template>
  <div>
    <div v-for="dataProductURI in selectedDataProductURIs" :key="dataProductURI" class="mb-2">
      <file-input-editor
        :id="dataProductURI"
        :value="dataProductURI"
        :experiment="experiment"
        :experiment-input="experimentInput"
        :read-only="readOnly"
        @input="updatedFile($event, dataProductURI)"
      />
    </div>
    <input-file-selector
      v-if="!readOnly"
      :selected-data-product-u-r-is="selectedDataProductURIs"
      multiple
      @selected="fileSelected"
      @uploadstart="$emit('uploadstart')"
      @uploadend="$emit('uploadend')"
    />
  </div>
</template>

<script>
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";
import FileInputEditor from "./FileInputEditor.vue";
import InputFileSelector from "./InputFileSelector";

export default {
  name: "MultiFileInputEditor",
  components: {
    FileInputEditor,
    InputFileSelector,
  },
  mixins: [InputEditorMixin],
  props: {
    value: {
      type: String,
    },
  },
  data() {
    return {};
  },
  computed: {
    selectedDataProductURIs() {
      return this.createValueArray(this.value);
    },
  },
  methods: {
    updatedFile(newValue, dataProductURI) {
      // Only remove is handled here, input-file-selector handles adding
      if (!newValue) {
        this.removeFile(dataProductURI);
      }
    },
    removeFile(dataProductURI) {
      const index = this.selectedDataProductURIs.findIndex((u) => u === dataProductURI);
      const copyDataProductURIs = this.selectedDataProductURIs.slice();
      copyDataProductURIs.splice(index, 1);
      this.data = copyDataProductURIs.join(",");
      this.valueChanged();
    },
    createValueArray(value) {
      if (value && typeof value === "string") {
        return value.split(",");
      } else {
        return [];
      }
    },
    fileSelected(dataProductURI) {
      const values = this.createValueArray(this.value);
      values.push(dataProductURI);
      this.data = values.join(",");
      this.valueChanged();
    },
  },
};
</script>
