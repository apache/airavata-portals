<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Application Details</h1>
        <form-group
          label="Application Name"
          label-for="application-name"
          :invalid-feedback="validationFeedback.appModuleName.invalidFeedback"
          :state="validationFeedback.appModuleName.state"
        >
          <input
            id="application-name"
            v-model="data.appModuleName"
            class="form-control"
            type="text"
            required
            :disabled="readonly"
            :state="validationFeedback.appModuleName.state"
          />
        </form-group>
        <form-group label="Application Version" label-for="application-version">
          <input
            id="application-version"
            v-model="data.appModuleVersion"
            class="form-control"
            type="text"
            :disabled="readonly"
          />
        </form-group>
        <form-group label="Application Description" label-for="application-description">
          <textarea
            id="application-description"
            v-model="data.appModuleDescription"
            class="form-control"
            :rows="3"
            :disabled="readonly"
          ></textarea>
        </form-group>
      </div>
    </div>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { errors, mixins } from "django-airavata-common-ui";

export default {
  name: "ApplicationModuleEditor",
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
      return errors.ValidationErrors.createValidationFeedback(this.data, this.validationErrors);
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
