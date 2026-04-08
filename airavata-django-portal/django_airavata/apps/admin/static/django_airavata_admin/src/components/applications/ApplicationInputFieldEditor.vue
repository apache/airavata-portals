<template>
  <div class="card"><div class="card-body">
    <div class="d-flex align-items-center" slot="header">
      <div v-if="!readonly" class="drag-handle me-1 text-muted">
        <i class="fa fa-grip-vertical"></i>
        <span class="visually-hidden">Drag handle for reordering</span>
      </div>
      <div class="me-auto">Input Field: {{ data.name }}</div>
      <a
        v-if="!readonly"
        class="text-secondary"
        @click="deleteApplicationInput"
      >
        <i class="fa fa-trash"></i>
        <span class="visually-hidden">Delete</span>
      </a>
    </div>
    <div class="collapse" :id="id + '-collapse'" :visible="!collapse">
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
      <div class="mb-3" label="Type" :label-for="id + '-type'">
        <select class="form-select"
          :id="id + '-type'"
          v-model="data.type"
          :options="inputTypeOptions"
          :disabled="readonly"
        />
      </div>
      <form-group
        label="Initial Value"
        :label-for="id + '-value'"
        v-if="showValueField"
      >
        <input class="form-control"
          :id="id + '-value'"
          type="text"
          v-model="data.value"
          :disabled="readonly"
        ></input>
      </div>
      <form-group
        label="Override Filename"
        :label-for="id + '-value'"
        v-if="showOverrideFilenameField"
      >
        <input class="form-control"
          :id="id + '-override-filename'"
          type="text"
          v-model="data.overrideFilename"
          :disabled="readonly"
        ></input>
      </div>
      <div class="mb-3" label="Application Argument" :label-for="id + '-argument'">
        <input class="form-control"
          :id="id + '-argument'"
          type="text"
          v-model="data.applicationArgument"
          :disabled="readonly"
        ></input>
      </div>
      <form-group
        class="flex-fill"
        label="Required on Command Line"
        :label-for="id + '-required-command-line'"
        description="Add this input's value to the command line in the generated job script."
      >
        <form-radio-group
          :id="id + '-required-command-line'"
          v-model="data.requiredToAddedToCommandLine"
          :options="trueFalseOptions"
          :disabled="readonly"
        >
        </div>
      </div>
      <div class="d-flex">
        <form-group
          class="flex-fill"
          label="Required"
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
          label="Read Only"
          :label-for="id + '-read-only'"
        >
          <form-radio-group
            :id="id + '-read-only'"
            v-model="data.isReadOnly"
            :options="trueFalseOptions"
            :disabled="readonly"
          >
          </div>
        </div>
      </div>
      <form-group
        label="User Friendly Description"
        :label-for="id + '-user-friendly-description'"
      >
        <textarea class="form-control"
          :id="id + '-user-friendly-description'"
          v-model="data.userFriendlyDescription"
          :rows="3"
          :disabled="readonly"
        />
      </div>
      <form-group
        label="Advanced Input Field Modification Metadata"
        :label-for="id + '-metadata'"
        description="Metadata for this input, in the JSON format"
      >
        <json-editor
          :id="id + '-metadata'"
          v-model="data.metaData"
          :rows="5"
          :disabled="readonly"
        />
      </div>
    </div>
  </div></div>
</template>

<script>
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";
import JSONEditor from "./JSONEditor.vue";

export default {
  name: "application-input-field-editor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.InputDataObjectType,
    },
    // Whether to put focus on the name field when mounting component
    focus: {
      type: Boolean,
    },
    collapse: {
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
    inputTypeOptions() {
      return models.InputDataObjectType.VALID_DATA_TYPES.map((dataType) => {
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
    showValueField() {
      return this.data.type.isSimpleValueType;
    },
    showOverrideFilenameField() {
      return this.data.type === models.DataType.URI;
    },
  },
  methods: {
    doFocus() {
      this.$refs.nameInput.focus();
      this.$el.scrollIntoView({ behavior: "smooth" });
    },
    deleteApplicationInput() {
      this.$emit("delete");
    },
  },
  mounted() {
    if (this.focus) {
      this.doFocus();
    }
  },
};
</script>

<style scoped>
.drag-handle {
  cursor: move;
}
</style>
