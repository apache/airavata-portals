<template>
  <div class="card">
    <div class="card-header d-flex align-items-center">
      <div class="me-auto">Output Field: {{ data.name }}</div>
      <a v-if="!readonly" class="text-secondary" @click="deleteApplicationOutput">
        <i class="fa fa-trash"></i>
        <span class="visually-hidden">Delete</span>
      </a>
    </div>
    <div class="card-body">
      <div class="mb-3" label="Name" :label-for="id + '-name'">
        <input
          :id="id + '-name'"
          ref="nameInput"
          v-model="data.name"
          class="form-control"
          type="text"
          required
          :disabled="readonly"
        />
      </div>
      <div class="mb-3" label="Value" :label-for="id + '-value'">
        <input
          :id="id + '-value'"
          v-model="data.value"
          class="form-control"
          type="text"
          :disabled="readonly"
        />
      </div>
      <div class="mb-3" label="Type" :label-for="id + '-type'">
        <select
          :id="id + '-type'"
          v-model="data.type"
          class="form-select"
          :options="outputTypeOptions"
          :disabled="readonly"
        />
      </div>
      <div class="mb-3" label="Application Argument" :label-for="id + '-argument'">
        <input
          :id="id + '-argument'"
          v-model="data.applicationArgument"
          class="form-control"
          type="text"
          :disabled="readonly"
        />
      </div>
      <div class="d-flex">
        <form-group class="flex-fill" label="Is Required" :label-for="id + '-required'">
          <form-radio-group
            :id="id + '-required'"
            v-model="data.isRequired"
            :options="trueFalseOptions"
            :disabled="readonly"
          />
        </form-group>
        <form-group
          class="flex-fill"
          label="Required on Command Line"
          :label-for="id + '-required-command-line'"
        >
          <form-radio-group
            :id="id + '-required-command-line'"
            v-model="data.requiredToAddedToCommandLine"
            :options="trueFalseOptions"
            :disabled="readonly"
          />
        </form-group>
      </div>
      <form-group
        label="Metadata"
        :label-for="id + '-metadata'"
        description="Metadata for this output, in the JSON format"
      >
        <json-editor
          :id="id + '-metadata'"
          v-model="data.metaData"
          :rows="5"
          :disabled="readonly"
        />
      </form-group>
      <button class="btn" size="sm" @click="setPlainText">Plain Text</button>
    </div>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";
import JSONEditor from "./JSONEditor.vue";
export default {
  name: "ApplicationOutputFieldEditor",
  components: {
    "json-editor": JSONEditor,
  },
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.OutputDataObjectType,
    },
    focus: {
      type: Boolean,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    outputTypeOptions() {
      return models.OutputDataObjectType.VALID_DATA_TYPES.map((dataType) => {
        return {
          value: dataType,
          text: dataType.name,
        };
      });
    },
    trueFalseOptions() {
      return [
        { text: "True", value: true },
        { text: "False", value: false },
      ];
    },
    id() {
      return "id-" + this.data.key;
    },
  },
  mounted() {
    if (this.focus) {
      this.doFocus();
    }
  },
  methods: {
    doFocus() {
      this.$refs.nameInput.focus();
      this.$el.scrollIntoView({ behavior: "smooth" });
    },
    deleteApplicationOutput() {
      this.$emit("delete");
    },
    setPlainText() {
      const metadata = this.data.metaData || {};
      metadata["file-metadata"] = { "mime-type": "text/plain" };
      // Clone so that JSONEditor updates with new value
      this.data.metaData = JSON.parse(JSON.stringify(metadata));
    },
  },
};
</script>
