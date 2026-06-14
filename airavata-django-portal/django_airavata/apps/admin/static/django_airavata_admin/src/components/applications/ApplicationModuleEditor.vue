<template>
  <div>
    <div>
      <h2 class="mb-4 text-lg font-semibold">Application Details</h2>
      <div class="space-y-4">
        <div class="space-y-1.5">
          <Label for="application-name">Application Name</Label>
          <Input
            id="application-name"
            type="text"
            v-model="data.app_module_name"
            required
            :disabled="readonly"
            :aria-invalid="validationFeedback.app_module_name.state === false"
          ></Input>
          <p
            v-if="validationFeedback.app_module_name.state === false"
            class="text-sm text-destructive"
          >
            {{ validationFeedback.app_module_name.invalidFeedback }}
          </p>
        </div>
        <div class="space-y-1.5">
          <Label for="application-version">Application Version</Label>
          <Input
            id="application-version"
            type="text"
            v-model="data.app_module_version"
            :disabled="readonly"
          ></Input>
        </div>
        <div class="space-y-1.5">
          <Label for="application-description">Application Description</Label>
          <Textarea
            id="application-description"
            v-model="data.app_module_description"
            :rows="3"
            :disabled="readonly"
          ></Textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { errors, mixins } from "django-airavata-common-ui";

export default {
  name: "application-module-editor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.ApplicationModule,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    validationErrors: {
      type: Object,
    },
  },
  computed: {
    validationFeedback() {
      return errors.ValidationErrors.createValidationFeedback(
        this.data,
        this.validationErrors,
      );
    },
  },
  methods: {
    save() {
      this.$emit("save");
    },
    cancel() {
      this.$emit("cancel");
    },
    deleteApplicationModule() {
      this.$emit("delete", this.data);
    },
  },
};
</script>
