<template>
  <Card>
    <CardHeader>
      <div class="flex items-center">
        <div class="mr-auto">Output Field: {{ data.name }}</div>
        <a
          href="#"
          v-if="!readonly"
          class="text-muted-foreground"
          @click.prevent="deleteApplicationOutput"
        >
          <Trash2 class="size-4" />
          <span class="sr-only">Delete</span>
        </a>
      </div>
    </CardHeader>
    <CardContent class="space-y-4">
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
        <Label :for="id + '-value'">Value</Label>
        <Input
          :id="id + '-value'"
          type="text"
          v-model="data.value"
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
            v-for="opt in outputTypeOptions"
            :key="opt.text"
            :value="opt.value"
          >
            {{ opt.text }}
          </option>
        </select>
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
      <div class="flex gap-4">
        <div class="flex-1 space-y-1.5">
          <Label>Is Required</Label>
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
        </div>
      </div>
      <div class="space-y-1.5">
        <Label :for="id + '-metadata'">Metadata</Label>
        <json-editor
          :id="id + '-metadata'"
          v-model="metadata"
          :rows="5"
          :disabled="readonly"
        />
        <p class="text-sm text-muted-foreground">
          Metadata for this output, in the JSON format
        </p>
      </div>
      <Button variant="outline" size="sm" @click="setPlainText"
        >Plain Text</Button
      >
    </CardContent>
  </Card>
</template>

<script>
import { Trash2 } from "@lucide/vue";
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
    Trash2,
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
    deleteApplicationOutput() {
      this.$emit("delete");
    },
    setPlainText() {
      const metadata = this.metadata || {};
      metadata["file-metadata"] = { "mime-type": "text/plain" };
      this.metadata = metadata;
    },
  },
  mounted() {
    if (this.focus) {
      this.doFocus();
    }
  },
};
</script>
