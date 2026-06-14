<template>
  <Card>
    <CardHeader>
      <div class="flex items-center">
        <div v-if="!readonly" class="drag-handle mr-1 text-muted-foreground">
          <GripVertical class="size-4" />
          <span class="sr-only">Drag handle for reordering</span>
        </div>
        <div class="mr-auto">Input Field: {{ data.name }}</div>
        <a
          href="#"
          v-if="!readonly"
          class="text-muted-foreground"
          @click.prevent="deleteApplicationInput"
        >
          <Trash2 class="size-4" />
          <span class="sr-only">Delete</span>
        </a>
      </div>
    </CardHeader>
    <CardContent v-show="!collapse" class="space-y-4">
      <div class="space-y-1.5">
        <Label :for="id + '-name'">Name</Label>
        <Input
          :id="id + '-name'"
          type="text"
          v-model="data.name"
          ref="nameInput"
          required
          :disabled="readonly"
        ></Input>
      </div>
      <div class="space-y-1.5">
        <Label :for="id + '-type'">Type</Label>
        <select
          :id="id + '-type'"
          v-model="data.type"
          :disabled="readonly"
          class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option
            v-for="opt in inputTypeOptions"
            :key="opt.text"
            :value="opt.value"
          >
            {{ opt.text }}
          </option>
        </select>
      </div>
      <div class="space-y-1.5" v-if="showValueField">
        <Label :for="id + '-value'">Initial Value</Label>
        <Input
          :id="id + '-value'"
          type="text"
          v-model="data.value"
          :disabled="readonly"
        ></Input>
      </div>
      <div class="space-y-1.5" v-if="showOverrideFilenameField">
        <Label :for="id + '-override-filename'">Override Filename</Label>
        <Input
          :id="id + '-override-filename'"
          type="text"
          v-model="data.override_filename"
          :disabled="readonly"
        ></Input>
      </div>
      <div class="space-y-1.5">
        <Label :for="id + '-argument'">Application Argument</Label>
        <Input
          :id="id + '-argument'"
          type="text"
          v-model="data.application_argument"
          :disabled="readonly"
        ></Input>
      </div>
      <div class="space-y-1.5">
        <Label>Required on Command Line</Label>
        <div class="flex gap-4">
          <label
            v-for="opt in trueFalseOptions"
            :key="String(opt.value)"
            class="flex items-center gap-2 text-sm"
          >
            <input
              type="radio"
              :value="opt.value"
              v-model="data.required_to_added_to_command_line"
              :disabled="readonly"
            />
            {{ opt.text }}
          </label>
        </div>
        <p class="text-sm text-muted-foreground">
          Add this input's value to the command line in the generated job
          script.
        </p>
      </div>
      <div class="flex gap-4">
        <div class="flex-1 space-y-1.5">
          <Label>Required</Label>
          <div class="flex gap-4">
            <label
              v-for="opt in trueFalseOptions"
              :key="String(opt.value)"
              class="flex items-center gap-2 text-sm"
            >
              <input
                type="radio"
                :value="opt.value"
                v-model="data.is_required"
                :disabled="readonly"
              />
              {{ opt.text }}
            </label>
          </div>
        </div>
        <div class="flex-1 space-y-1.5">
          <Label>Read Only</Label>
          <div class="flex gap-4">
            <label
              v-for="opt in trueFalseOptions"
              :key="String(opt.value)"
              class="flex items-center gap-2 text-sm"
            >
              <input
                type="radio"
                :value="opt.value"
                v-model="data.is_read_only"
                :disabled="readonly"
              />
              {{ opt.text }}
            </label>
          </div>
        </div>
      </div>
      <div class="space-y-1.5">
        <Label :for="id + '-user-friendly-description'"
          >User Friendly Description</Label
        >
        <Textarea
          :id="id + '-user-friendly-description'"
          v-model="data.user_friendly_description"
          :rows="3"
          :disabled="readonly"
        />
      </div>
      <div class="space-y-1.5">
        <Label :for="id + '-metadata'"
          >Advanced Input Field Modification Metadata</Label
        >
        <json-editor
          :id="id + '-metadata'"
          v-model="metadata"
          :rows="5"
          :disabled="readonly"
        />
        <p class="text-sm text-muted-foreground">
          Metadata for this input, in the JSON format
        </p>
      </div>
    </CardContent>
  </Card>
</template>

<script>
import { GripVertical, Trash2 } from "@lucide/vue";
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
    GripVertical,
    Trash2,
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
    // meta_data is a raw JSON string on the wire; JSONEditor works with objects.
    metadata: {
      get() {
        if (!this.data.meta_data) {
          return null;
        }
        return typeof this.data.meta_data === "string"
          ? JSON.parse(this.data.meta_data)
          : this.data.meta_data;
      },
      set(value) {
        this.data.meta_data = value ? JSON.stringify(value) : null;
      },
    },
  },
  methods: {
    doFocus() {
      this.$refs.nameInput.$el.focus();
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
