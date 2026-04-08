<template>
  <div class="card"><div class="card-body">
    <div class="d-flex align-items-center" slot="header">
      <div class="me-auto">Output Field: {{ data.name }}</div>
      <a
        v-if="!readonly"
        class="text-secondary"
        @click="deleteApplicationOutput"
      >
        <i class="fa fa-trash"></i>
        <span class="visually-hidden">Delete</span>
      </a>
    </div>
    <div class="mb-3" label="Name" :label-for="id + '-name'">
      <input class="form-control"
        :id="id + '-name'"
        type="text"
        v-model="data.name"
        ref="nameInput"
        required
        :disabled="readonly"
      ></input>
    </div>
    <div class="mb-3" label="Value" :label-for="id + '-value'">
      <input class="form-control"
        :id="id + '-value'"
        type="text"
        v-model="data.value"
        :disabled="readonly"
      ></input>
    </div>
    <div class="mb-3" label="Type" :label-for="id + '-type'">
      <select class="form-select"
        :id="id + '-type'"
        v-model="data.type"
        :options="outputTypeOptions"
        :disabled="readonly"
      />
    </div>
    <div class="mb-3" label="Application Argument" :label-for="id + '-argument'">
      <input class="form-control"
        :id="id + '-argument'"
        type="text"
        v-model="data.applicationArgument"
        :disabled="readonly"
      ></input>
    </div>
    <div class="d-flex">
      <form-group
        class="flex-fill"
        label="Is Required"
        :label-for="id + '-required'"
      >
        <form-radio-group
          :id="id + '-required'"
          v-model="data.isRequired"
          :options="trueFalseOptions"
          :disabled="readonly"
        >
        </div>
      </div>
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
        >
        </div>
      </div>
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
    </div>
    <button class="btn" size="sm" @click="setPlainText">Plain Text</button>
  </div></div>
</template>

<script>
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";
import JSONEditor from "./JSONEditor.vue";
export default {
  name: "application-output-field-editor",
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
  components: {
    "json-editor": JSONEditor,
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
  mounted() {
    if (this.focus) {
      this.doFocus();
    }
  },
};
</script>
