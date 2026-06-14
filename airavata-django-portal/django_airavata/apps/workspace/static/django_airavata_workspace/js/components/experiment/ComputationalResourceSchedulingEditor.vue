<template>
  <div>
    <div>
      <div class="space-y-1.5">
        <Label for="compute-resource">Compute Resource</Label>
        <select
          id="compute-resource"
          v-model="resourceHostId"
          required
          :aria-invalid="getValidationState('resource_host_id') === false"
          :disabled="
            !computeResourceOptions || computeResourceOptions.length === 0
          "
          :class="nativeSelectClass"
          @change="computeResourceChanged($event.target.value)"
        >
          <option :value="null" disabled>Select a Compute Resource</option>
          <option
            v-for="option in computeResourceOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.text }}
          </option>
        </select>
        <p
          v-if="getValidationState('resource_host_id') === false"
          class="text-sm text-destructive"
        >
          {{ getValidationFeedback("resource_host_id") }}
        </p>
      </div>
    </div>
    <div class="mt-4">
      <queue-settings-editor
        v-model="data"
        v-if="appDeploymentId"
        :app-module-id="appModuleId"
        :app-deployment-id="appDeploymentId"
        :compute-resource-policy="selectedComputeResourcePolicy"
        :batch-queue-resource-policies="batchQueueResourcePolicies"
        @update:model-value="queueSettingsChanged"
        @valid="queueSettingsValidityChanged(true)"
        @invalid="queueSettingsValidityChanged(false)"
      >
      </queue-settings-editor>
    </div>
  </div>
</template>

<script>
import QueueSettingsEditor from "./QueueSettingsEditor.vue";
import {
  errors,
  models,
  services,
  utils as apiUtils,
} from "django-airavata-api";
import { mixins, utils } from "django-airavata-common-ui";
import { NATIVE_SELECT_CLASS } from "../../lib/utils";

export default {
  name: "computational-resource-scheduling-editor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.ComputationalResourceSchedulingModel,
    },
    appModuleId: {
      type: String,
      required: true,
    },
    groupResourceProfileId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      computeResources: {},
      applicationDeployments: [],
      selectedGroupResourceProfileData: null,
      resourceHostId: this.value.resource_host_id,
      invalidQueueSettings: false,
      workspacePreferences: null,
    };
  },
  components: {
    QueueSettingsEditor,
  },
  mounted: function () {
    this.loadWorkspacePreferences().then(() => {
      this.loadApplicationDeployments(
        this.appModuleId,
        this.groupResourceProfileId,
      );
    });
    this.loadComputeResourceNames();
    this.loadGroupResourceProfile();
    this.validate();
  },
  computed: {
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>, plus the
      // invalid-state ring so it mirrors `:aria-invalid` on shadcn controls.
      return `${NATIVE_SELECT_CLASS} aria-invalid:border-destructive aria-invalid:ring-destructive/40`;
    },
    localComputationalResourceScheduling() {
      return this.data;
    },
    computeResourceOptions: function () {
      const computeResourceOptions = this.applicationDeployments.map((dep) => {
        return {
          value: dep.compute_host_id,
          text:
            dep.compute_host_id in this.computeResources
              ? this.computeResources[dep.compute_host_id]
              : "",
        };
      });
      computeResourceOptions.sort((a, b) => a.text.localeCompare(b.text));
      return computeResourceOptions;
    },
    selectedComputeResourcePolicy: function () {
      if (this.selectedGroupResourceProfileData === null) {
        return null;
      }
      return this.selectedGroupResourceProfileData.compute_resource_policies.find(
        (crp) => {
          return (
            crp.compute_resource_id ===
            this.localComputationalResourceScheduling.resource_host_id
          );
        },
      );
    },
    batchQueueResourcePolicies: function () {
      if (this.selectedGroupResourceProfileData === null) {
        return null;
      }
      return this.selectedGroupResourceProfileData.batch_queue_resource_policies.filter(
        (bqrp) => {
          return (
            bqrp.compute_resource_id ===
            this.localComputationalResourceScheduling.resource_host_id
          );
        },
      );
    },
    appDeploymentId: function () {
      // We'll only be able to figure out the appDeploymentId when a
      // resourceHostId is selected and the application deployments are
      // loaded
      if (!this.resourceHostId || this.applicationDeployments.length === 0) {
        return null;
      }
      // Find application deployment that corresponds to this compute resource
      let selectedApplicationDeployment = this.applicationDeployments.find(
        (dep) => dep.compute_host_id === this.resourceHostId,
      );
      if (!selectedApplicationDeployment) {
        throw new Error("Failed to find application deployment!");
      }
      return selectedApplicationDeployment.app_deployment_id;
    },
    validation() {
      const queueInfo = {}; // QueueSettingsEditor will validate queue information
      return this.localComputationalResourceScheduling.validate(queueInfo);
    },
    valid() {
      return (
        !this.invalidQueueSettings && Object.keys(this.validation).length === 0
      );
    },
  },
  methods: {
    computeResourceChanged: function (selectedComputeResourceId) {
      this.data.resource_host_id = selectedComputeResourceId;
    },
    loadApplicationDeployments: function (appModuleId, groupResourceProfileId) {
      services.ApplicationDeploymentService.list(
        {
          appModuleId: appModuleId,
          groupResourceProfileId: groupResourceProfileId,
        },
        { ignoreErrors: true },
      )
        .then((applicationDeployments) => {
          this.applicationDeployments = applicationDeployments;
        })
        .catch((error) => {
          // Ignore unauthorized errors, force user to pick another GroupResourceProfile
          if (!errors.ErrorUtils.isUnauthorizedError(error)) {
            return Promise.reject(error);
          }
        })
        // Report all other error types
        .catch(apiUtils.FetchUtils.reportError);
    },
    loadGroupResourceProfile: function () {
      services.GroupResourceProfileService.retrieve(
        { lookup: this.groupResourceProfileId },
        { ignoreErrors: true },
      )
        .then((groupResourceProfile) => {
          this.selectedGroupResourceProfileData = groupResourceProfile;
        })
        .catch((error) => {
          // Ignore unauthorized errors, force user to pick a different GroupResourceProfile
          if (!errors.ErrorUtils.isUnauthorizedError(error)) {
            return Promise.reject(error);
          }
        })
        // Report all other error types
        .catch(apiUtils.FetchUtils.reportError);
    },
    loadComputeResourceNames: function () {
      services.ComputeResourceService.names().then(
        (computeResourceNames) =>
          (this.computeResources = computeResourceNames),
      );
    },
    loadWorkspacePreferences() {
      return services.WorkspacePreferencesService.get().then(
        (workspacePreferences) =>
          (this.workspacePreferences = workspacePreferences),
      );
    },
    queueSettingsChanged: function () {
      // QueueSettingsEditor updates the full
      // ComputationalResourceSchedulingModel instance but doesn't know
      // the resourceHostId so we need to copy it back into the instance
      // whenever it changes
      this.localComputationalResourceScheduling.resource_host_id =
        this.resourceHostId;
      this.$emit("input", this.data);
    },
    queueSettingsValidityChanged(valid) {
      this.invalidQueueSettings = !valid;
      this.validate();
    },
    validate() {
      if (!this.valid) {
        this.$emit("invalid");
      } else {
        this.$emit("valid");
      }
    },
    emitValueChanged: function () {
      this.validate();
      this.$emit("input", this.localComputationalResourceScheduling);
    },
    getValidationFeedback: function (properties) {
      return utils.getProperty(this.validation, properties);
    },
    getValidationState: function (properties) {
      return this.getValidationFeedback(properties) ? false : null;
    },
  },
  watch: {
    // Re-validate whenever the editor's working copy changes. (Replaces the Vue 2
    // `this.$on("input", ...)` self-listener, which is removed in Vue 3.)
    data: {
      handler() {
        this.validate();
      },
      deep: true,
    },
    computeResourceOptions: function (newOptions) {
      // If the selected resourceHostId is not in the new list of
      // computeResourceOptions, reset it to null
      if (
        this.resourceHostId !== null &&
        !newOptions.find((opt) => opt.value === this.resourceHostId)
      ) {
        this.resourceHostId = null;
      }
      // Apply preferred (most recently used) compute resource
      if (
        this.resourceHostId === null &&
        this.workspacePreferences.most_recent_compute_resource_id &&
        newOptions.find(
          (opt) =>
            opt.value ===
            this.workspacePreferences.most_recent_compute_resource_id,
        )
      ) {
        this.resourceHostId =
          this.workspacePreferences.most_recent_compute_resource_id;
      }
      // If none selected, just pick the first one
      if (this.resourceHostId === null && newOptions.length > 0) {
        this.resourceHostId = newOptions[0].value;
      }
      this.computeResourceChanged(this.resourceHostId);
    },
    groupResourceProfileId: function (newGroupResourceProfileId) {
      this.loadApplicationDeployments(
        this.appModuleId,
        newGroupResourceProfileId,
      );
      if (
        this.selectedGroupResourceProfileData &&
        this.selectedGroupResourceProfileData.group_resource_profile_id !==
          newGroupResourceProfileId
      ) {
        this.loadGroupResourceProfile();
      }
    },
  },
};
</script>

<style></style>
