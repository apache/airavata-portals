<template>
  <div class="has-fixed-footer">
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">
          <div
            v-if="localGroupResourceProfile"
            class="group-resource-profile-name text-muted text-uppercase"
          >
            <i class="fa fa-server" aria-hidden="true"></i>
            {{ localGroupResourceProfile.group_resource_profile_name }}
          </div>
          {{ computeResource.host_name }}
        </h1>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <b-form-group
              label="Login Username"
              label-for="login-username"
              :invalid-feedback="
                validationFeedback.login_user_name.invalidFeedback
              "
              :state="validationFeedback.login_user_name.state"
            >
              <b-form-input
                id="login-username"
                type="text"
                required
                v-model="data.login_user_name"
                :state="validationFeedback.login_user_name.state"
                :disabled="!userHasWriteAccess"
                @input="validate"
              >
              </b-form-input>
            </b-form-group>
            <b-form-group
              label="SSH Credential"
              label-for="credential-store-token"
            >
              <ssh-credential-selector
                v-model="data.resource_specific_credential_store_token"
                v-if="localGroupResourceProfile"
                :readonly="!userHasWriteAccess"
                :null-option-default-credential-token="
                  localGroupResourceProfile.default_credential_store_token
                "
                :null-option-disabled="
                  !localGroupResourceProfile.default_credential_store_token
                "
              >
                <template
                  slot="null-option-label"
                  slot-scope="nullOptionLabelScope"
                >
                  <span v-if="nullOptionLabelScope.defaultCredentialSummary">
                    Use the default SSH credential for
                    {{ localGroupResourceProfile.group_resource_profile_name }} ({{
                      nullOptionLabelScope.defaultCredentialSummary.username
                    }}
                    -
                    {{
                      nullOptionLabelScope.defaultCredentialSummary.description
                    }})
                  </span>
                  <span v-else> Select a SSH credential </span>
                </template>
              </ssh-credential-selector>
            </b-form-group>
            <b-form-group
              label="Resource Type"
              label-for="resource-type"
              :invalid-feedback="validationFeedback.resource_type.invalidFeedback"
              :state="validationFeedback.resource_type.state"
            >
              <b-form-select
                id="resource-type"
                v-model="data.resource_type"
                :options="resourceTypeOptions"
                :disabled="!userHasWriteAccess"
                :state="validationFeedback.resource_type.state"
                @change="onResourceTypeChange"
              >
                <template slot="first">
                  <option :value="null">Select a resource type</option>
                </template>
              </b-form-select>
            </b-form-group>
            <!-- SLURM-specific fields -->
            <template v-if="isResourceType('SLURM')">
              <b-form-group
                label="Allocation Project Number"
                label-for="allocation-number"
              >
                <b-form-input
                  id="allocation-number"
                  type="text"
                  v-model="data.allocation_project_number"
                  :disabled="!userHasWriteAccess"
                >
                </b-form-input>
              </b-form-group>
            </template>
            <!-- AWS-specific fields -->
            <template v-if="isResourceType('AWS')">
              <b-form-group
                label="Region"
                label-for="aws-region"
              >
                <b-form-input
                  id="aws-region"
                  type="text"
                  v-model="data.specific_preferences.region"
                  :disabled="!userHasWriteAccess"
                >
                </b-form-input>
              </b-form-group>
              <b-form-group
                label="Preferred AMI ID"
                label-for="preferred-ami-id"
              >
                <b-form-input
                  id="preferred-ami-id"
                  type="text"
                  v-model="data.specific_preferences.preferred_ami_id"
                  :disabled="!userHasWriteAccess"
                >
                </b-form-input>
              </b-form-group>
              <b-form-group
                label="Preferred Instance Type"
                label-for="preferred-instance-type"
              >
                <b-form-input
                  id="preferred-instance-type"
                  type="text"
                  v-model="data.specific_preferences.preferred_instance_type"
                  :disabled="!userHasWriteAccess"
                >
                </b-form-input>
              </b-form-group>
            </template>
            <b-form-group
              label="Scratch Location"
              label-for="scratch-location"
              :invalid-feedback="
                validationFeedback.scratch_location.invalidFeedback
              "
              :state="validationFeedback.scratch_location.state"
            >
              <b-form-input
                id="scratch-location"
                type="text"
                required
                v-model="data.scratch_location"
                :disabled="!userHasWriteAccess"
                :state="validationFeedback.scratch_location.state"
                @input="validate"
              >
              </b-form-input>
            </b-form-group>
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Policy</h5>
            <compute-resource-policy-editor
              :batch-queues="computeResource.batch_queues"
              :compute-resource-policy="localComputeResourcePolicy"
              :batch-queue-resource-policies="localBatchQueueResourcePolicies"
              :readonly="!userHasWriteAccess"
              @compute-resource-policy-updated="
                localComputeResourcePolicy = $event
              "
              @batch-queue-resource-policies-updated="
                localBatchQueueResourcePolicies = $event
              "
              @valid="computeResourcePolicyInvalid = false"
              @invalid="computeResourcePolicyInvalid = true"
            />
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <compute-resource-reservation-list
              v-if="isResourceType('SLURM')"
              :reservations="data.reservations"
              :queues="queueNames"
              :readonly="!userHasWriteAccess"
              @added="addReservation"
              @deleted="deleteReservation"
              @updated="updateReservation"
              @valid="reservationsInvalid = false"
              @invalid="reservationsInvalid = true"
            />
          </div>
        </div>
      </div>
    </div>
    <div class="fixed-footer">
      <b-button
        variant="primary"
        @click="save"
        :disabled="!valid || !userHasWriteAccess"
      >Save
      </b-button
      >
      <delete-button
        class="ml-2"
        :disabled="!userHasWriteAccess"
        @delete="remove">
        Are you sure you want to remove the preferences for compute resource
        <strong>{{ computeResource.host_name }}</strong
        >?
      </delete-button>
      <b-button class="ml-2" variant="secondary" @click="cancel"
      >Cancel
      </b-button
      >
    </div>
  </div>
</template>

<script>
import DjangoAiravataAPI, {errors, models, services} from "django-airavata-api";
import SSHCredentialSelector from "../../credentials/SSHCredentialSelector.vue";
import ComputeResourceReservationList from "./ComputeResourceReservationList";
import ComputeResourcePolicyEditor from "./ComputeResourcePolicyEditor";
import {components, errors as uiErrors, mixins, notifications,} from "django-airavata-common-ui";

export default {
  name: "compute-preference",
  components: {
    "delete-button": components.DeleteButton,
    "ssh-credential-selector": SSHCredentialSelector,
    ComputeResourceReservationList,
    ComputeResourcePolicyEditor,
  },
  props: {
    id: {
      type: String,
    },
    host_id: {
      type: String,
      required: true,
    },
    groupResourceProfile: {
      type: models.GroupResourceProfile,
    },
    computeResourcePolicy: {
      type: models.ComputeResourcePolicy,
    },
    batchQueueResourcePolicies: {
      type: Array,
    },
  },
  mounted: function () {
    const computeResourcePromise = this.fetchComputeResource(this.host_id);
    if (this.localGroupResourceProfile) {
      this.userHasWriteAccess = this.localGroupResourceProfile.user_has_write_access;
    }
    if (!this.value && this.id && this.host_id) {
      services.GroupResourceProfileService.retrieve({lookup: this.id}).then(
        (groupResourceProfile) => {
          this.localGroupResourceProfile = groupResourceProfile;
          this.userHasWriteAccess = this.localGroupResourceProfile.user_has_write_access;
          const computeResourcePreference = groupResourceProfile.getComputePreference(
            this.host_id
          );
          if (computeResourcePreference) {
            this.data = computeResourcePreference;
          }
          const computeResourcePolicy = groupResourceProfile.getComputeResourcePolicy(
            this.host_id
          );
          if (computeResourcePolicy) {
            this.localComputeResourcePolicy = computeResourcePolicy;
          } else {
            this.createDefaultComputeResourcePolicy(computeResourcePromise);
          }
          this.localBatchQueueResourcePolicies = groupResourceProfile.getBatchQueueResourcePolicies(
            this.host_id
          );
        }
      );
    } else if (!this.computeResourcePolicy) {
      this.createDefaultComputeResourcePolicy(computeResourcePromise);
    }
    if (!this.id) {
      this.userHasWriteAccess = true;
    }
    this.$on("input", this.validate);

  },
  data: function () {
    return {
      data: this.value
        ? this.value.clone()
        : new models.GroupComputeResourcePreference({
          compute_resource_id: this.host_id,
        }),
      localGroupResourceProfile: this.groupResourceProfile
        ? this.groupResourceProfile.clone()
        : null,
      localComputeResourcePolicy: this.computeResourcePolicy
        ? this.computeResourcePolicy.clone()
        : null,
      localBatchQueueResourcePolicies: this.batchQueueResourcePolicies
        ? this.batchQueueResourcePolicies.map((pol) => pol.clone())
        : [],
      computeResource: {
        batch_queues: [],
        job_submission_interfaces: [],
      },
      validationErrors: null,
      reservationsInvalid: false,
      computeResourcePolicyInvalid: false,
      userHasWriteAccess: false,
      resourceTypeOptions: models.ResourceType.values.map(rt => ({
        value: rt,
        text: rt.name,
      })),
    };
  },
  computed: {
    groupComputeResourceValidation() {
      return this.data.validate();
    },
    validationFeedback() {
      return uiErrors.ValidationErrors.createValidationFeedback(
        this.data,
        this.groupComputeResourceValidation
      );
    },
    valid() {
      return (
        Object.keys(this.groupComputeResourceValidation).length === 0 &&
        !this.reservationsInvalid &&
        !this.computeResourcePolicyInvalid
      );
    },
    queueNames() {
      return this.computeResource.batch_queues.map((bq) => bq.queue_name);
    },
  },
  mixins: [mixins.VModelMixin],
  methods: {
    fetchComputeResource: function (id) {
      return DjangoAiravataAPI.utils.FetchUtils.get(
        "/api/compute-resources/" + encodeURIComponent(id) + "/"
      ).then((value) => {
        return (this.computeResource = value);
      });
    },
    save: function () {
      let groupResourceProfile = this.localGroupResourceProfile.clone();
      groupResourceProfile.mergeComputeResourcePreference(
        this.data,
        this.localComputeResourcePolicy,
        this.localBatchQueueResourcePolicies
      );
      return this.saveOrUpdate(groupResourceProfile)
        .then((groupResourceProfile) => {
          // Navigate back to GroupResourceProfile with success message
          this.$router.push({
            name: "group_resource_preference",
            params: {
              value: groupResourceProfile,
              id: groupResourceProfile.group_resource_profile_id,
            },
          });
        })
        .catch((error) => {
          if (
            errors.ErrorUtils.isValidationError(error) &&
            "compute_preferences" in error.details.response
          ) {
            const computePreferencesIndex = groupResourceProfile.compute_preferences.findIndex(
              (cp) => cp.compute_resource_id === this.host_id
            );
            this.validationErrors =
              error.details.response.compute_preferences[
                computePreferencesIndex
                ];
          } else {
            this.validationErrors = null;
            notifications.NotificationList.addError(error);
          }
        });
    },
    saveOrUpdate(groupResourceProfile) {
      if (this.id) {
        return DjangoAiravataAPI.services.GroupResourceProfileService.update(
          {data: groupResourceProfile, lookup: this.id},
          {ignoreErrors: true}
        );
      } else {
        return DjangoAiravataAPI.services.GroupResourceProfileService.create(
          {data: groupResourceProfile},
          {ignoreErrors: true}
        );
      }
    },
    remove: function () {
      let groupResourceProfile = this.localGroupResourceProfile.clone();
      const removedChildren = groupResourceProfile.removeComputeResource(
        this.host_id
      );
      if (removedChildren) {
        DjangoAiravataAPI.services.GroupResourceProfileService.update({
          data: groupResourceProfile,
          lookup: this.id,
        }).then((groupResourceProfile) => {
          // Navigate back to GroupResourceProfile with success message
          this.$router.push({
            name: "group_resource_preference",
            params: {
              value: groupResourceProfile,
              id: this.id,
            },
          });
        });
      } else {
        // Since nothing was removed, just handle this like a cancel
        this.cancel();
      }
    },
    cancel: function () {
      if (this.id) {
        this.$router.push({
          name: "group_resource_preference",
          params: {id: this.id},
        });
      } else {
        this.$router.push({
          name: "new_group_resource_preference",
          params: {value: this.localGroupResourceProfile},
        });
      }
    },
    createDefaultComputeResourcePolicy: function (computeResourcePromise) {
      computeResourcePromise.then((computeResource) => {
        const defaultComputeResourcePolicy = new models.ComputeResourcePolicy();
        defaultComputeResourcePolicy.compute_resource_id = this.host_id;
        defaultComputeResourcePolicy.group_resource_profile_id = this.id;
        defaultComputeResourcePolicy.allowed_batch_queues = computeResource.batch_queues.map(
          (queue) => queue.queue_name
        );
        this.localComputeResourcePolicy = defaultComputeResourcePolicy;
      });
    },
    validate() {
      if (this.valid) {
        this.$emit("valid");
      } else {
        this.$emit("invalid");
      }
    },
    addReservation(reservation) {
      this.data.reservations.push(reservation);
      this.data.reservations.sort((a, b) =>
        a.start_time < b.start_time ? -1 : 1
      );
    },
    deleteReservation(reservation) {
      const reservationIndex = this.data.reservations.findIndex(
        (r) => r.key === reservation.key
      );
      this.data.reservations.splice(reservationIndex, 1);
    },
    updateReservation(reservation) {
      const reservationIndex = this.data.reservations.findIndex(
        (r) => r.key === reservation.key
      );
      this.data.reservations.splice(reservationIndex, 1, reservation);
    },
    onResourceTypeChange() {
      if (!this.data.resource_type) {
        this.data.specific_preferences = null;
        this.validate();
        return;
      }
      if (this.data.resetSpecificPreferences) {
        this.data.resetSpecificPreferences();
      } else {
        const resourceTypeName = this.data.resource_type.name;
        const modelClassName = this._getPreferenceModelClassName(resourceTypeName);
        if (modelClassName && models[modelClassName]) {
          const PreferenceModel = models[modelClassName];
          this.data.specific_preferences = new PreferenceModel();
        } else {
          this.data.specific_preferences = null;
        }
      }
      this.validate();
    },
    _getPreferenceModelClassName(resourceTypeName) {
      // Convert resource type name to model class name
      // 'SLURM' -> 'SlurmComputeResourcePreference'
      // 'AWS' -> 'AwsComputeResourcePreference'
      if (!resourceTypeName) return null;
      const capitalized = resourceTypeName.charAt(0) + resourceTypeName.slice(1).toLowerCase();
      return capitalized + 'ComputeResourcePreference';
    },
    isResourceType(resourceTypeName) {
      if (this.data.isResourceType) {
        return this.data.isResourceType(resourceTypeName);
      }
      return this.data.resource_type && this.data.resource_type.name === resourceTypeName;
    },
  },
  beforeRouteEnter: function (to, from, next) {
    // If we don't have the Group Resource Profile id or instance, then the
    // Group Resource Profile wasn't created and we need to just go back to
    // the dashboard
    if (!to.params.id && !to.params.groupResourceProfile) {
      next({name: "group_resource_preference_dashboard"});
    } else {
      next();
    }
  },
};
</script>

<style scoped>
.group-resource-profile-name {
  font-size: 12px;
}
</style>
