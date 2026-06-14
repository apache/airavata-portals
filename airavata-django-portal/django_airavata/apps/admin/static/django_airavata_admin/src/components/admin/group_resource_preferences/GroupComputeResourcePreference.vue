<template>
  <main-layout
    :title="title || 'Group Resource Profile'"
    subtitle="Configure compute resource preferences for this group."
  >
    <div class="space-y-4 pb-20">
      <p v-if="owner" class="text-sm text-muted-foreground">
        Created by <span :title="ownerTitle">{{ ownerUserId }}</span>
      </p>
      <Card>
        <CardContent class="space-y-4">
          <div class="space-y-1.5">
            <Label for="profile-name">Name</Label>
            <Input
              id="profile-name"
              type="text"
              v-model="data.group_resource_profile_name"
              :disabled="!userHasWriteAccess"
              required
              placeholder="Name of this Group Resource Profile"
            >
            </Input>
          </div>
          <div class="space-y-1.5">
            <Label for="default-credential-store-token"
              >Default SSH Credential</Label
            >
            <ssh-credential-selector
              id="default-credential-store-token"
              v-model="data.default_credential_store_token"
              :readonly="!userHasWriteAccess"
            >
            </ssh-credential-selector>
          </div>
          <share-button ref="shareButton" :entity-id="id" />
        </CardContent>
      </Card>
      <list-layout
        :items="data.compute_preferences"
        :newButtonDisabled="!userHasWriteAccess"
        title="Compute Preferences"
        new-item-button-text="New Compute Preference"
        @add-new-item="createComputePreference"
      >
        <template v-slot:title>
          <h2 class="text-lg font-semibold">Compute Preferences</h2>
        </template>
        <template v-slot:item-list="slotProps">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  v-for="field in computePreferencesFields"
                  :key="field.key"
                >
                  {{ field.label }}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="item in sortedItems(slotProps.items)"
                :key="item.compute_resource_id"
              >
                <TableCell>
                  <compute-resource-name
                    :compute-resource-id="item.compute_resource_id"
                  />
                </TableCell>
                <TableCell>{{ item.login_user_name }}</TableCell>
                <TableCell>{{ item.allocation_project_number }}</TableCell>
                <TableCell>
                  <compute-resource-policy-summary
                    :compute-resource-id="item.compute_resource_id"
                    :group-resource-profile="data"
                  />
                </TableCell>
                <TableCell>
                  <compute-resource-reservations-summary
                    :reservations="item.reservations"
                  />
                </TableCell>
                <TableCell>
                  <router-link
                    class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                    v-if="userHasWriteAccess"
                    :to="{
                      name: 'compute_preference',
                      params: {
                        value: item,
                        id: id,
                        host_id: item.compute_resource_id,
                        groupResourceProfile: data,
                        computeResourcePolicy: data.getComputeResourcePolicy(
                          item.compute_resource_id,
                        ),
                        batchQueueResourcePolicies:
                          data.getBatchQueueResourcePolicies(
                            item.compute_resource_id,
                          ),
                      },
                    }"
                  >
                    Edit
                    <Pencil class="size-4" aria-hidden="true" />
                  </router-link>

                  <router-link
                    class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                    v-if="!userHasWriteAccess"
                    :to="{
                      name: 'compute_preference',
                      params: {
                        value: item,
                        id: id,
                        host_id: item.compute_resource_id,
                        groupResourceProfile: data,
                        computeResourcePolicy: data.getComputeResourcePolicy(
                          item.compute_resource_id,
                        ),
                        batchQueueResourcePolicies:
                          data.getBatchQueueResourcePolicies(
                            item.compute_resource_id,
                          ),
                      },
                    }"
                  >
                    View
                    <Eye class="size-4" aria-hidden="true" />
                  </router-link>

                  <delete-link
                    v-if="userHasWriteAccess"
                    @delete="removeComputePreference(item.compute_resource_id)"
                  >
                    Are you sure you want to remove the preferences for compute
                    resource
                    <strong>
                      <compute-resource-name
                        :compute-resource-id="item.compute_resource_id"
                      /> </strong
                    >?
                  </delete-link>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </template>
      </list-layout>
      <div
        class="bg-background fixed inset-x-0 bottom-0 flex gap-2 border-t p-4 shadow-md"
      >
        <Button
          variant="default"
          :disabled="!userHasWriteAccess"
          @click="saveGroupResourceProfile"
          >Save</Button
        >
        <delete-button
          v-if="id"
          :disabled="!userHasWriteAccess"
          @delete="removeGroupResourceProfile"
        >
          Are you sure you want to remove Group Resource Profile
          <strong>{{ data.group_resource_profile_name }}</strong
          >?
        </delete-button>
        <Button variant="secondary" @click="cancel">Cancel</Button>
      </div>
      <compute-resources-modal
        ref="modalSelectComputeResource"
        @selected="onSelectComputeResource"
        :excluded-resource-ids="excludedComputeResourceIds"
      />
    </div>
  </main-layout>
</template>

<script>
import { Eye, Pencil } from "@lucide/vue";
import { components as comps, layouts } from "django-airavata-common-ui";
import { models, services } from "django-airavata-api";
import ComputeResourcePolicySummary from "./ComputeResourcePolicySummary.vue";
import ComputeResourceReservationsSummary from "./ComputeResourceReservationsSummary.vue";
import ComputeResourcesModal from "../ComputeResourcesModal.vue";
import SSHCredentialSelector from "../../credentials/SSHCredentialSelector.vue";

export default {
  name: "group-compute-resource-preference",
  props: {
    value: {
      type: models.GroupResourceProfile,
      default: function () {
        return new models.GroupResourceProfile();
      },
    },
    id: {
      type: String,
    },
  },
  mounted: function () {
    if (this.id) {
      if (!this.value.group_resource_profile_id) {
        services.GroupResourceProfileService.retrieve({ lookup: this.id }).then(
          (grp) => {
            this.data = grp;
            this.userHasWriteAccess = this.data.user_has_write_access;
          },
        );
      }
      // Load information about the owner of this GroupResourceProfile
      services.SharedEntityService.retrieve({
        lookup: this.id,
      }).then((sharedEntity) => {
        this.sharedEntity = sharedEntity;
      });
    } else {
      this.userHasWriteAccess = true;
    }
  },
  data: function () {
    let data = this.value.clone();
    return {
      data: data,
      service: services.GroupResourceProfileService,
      sharedEntity: null,
      userHasWriteAccess: data.user_has_write_access,
      computePreferencesFields: [
        {
          label: "Name",
          key: "compute_resource_id",
          sortable: true,
        },
        {
          label: "Username",
          key: "login_user_name",
        },
        {
          label: "Allocation",
          key: "allocation_project_number",
        },
        {
          label: "Policy",
          key: "policy", // custom rendering
        },
        {
          label: "Reservations",
          key: "reservations", // custom rendering
        },
        {
          label: "Action",
          key: "action",
        },
      ],
    };
  },

  components: {
    Eye,
    Pencil,
    "delete-button": comps.DeleteButton,
    "delete-link": comps.DeleteLink,
    "share-button": comps.ShareButton,
    "main-layout": comps.MainLayout,
    "list-layout": layouts.ListLayout,
    ComputeResourcePolicySummary,
    ComputeResourcesModal,
    "ssh-credential-selector": SSHCredentialSelector,
    ComputeResourceReservationsSummary,
    "compute-resource-name": comps.ComputeResourceName,
  },
  computed: {
    excludedComputeResourceIds() {
      const currentPrefs = this.data.compute_preferences
        ? this.data.compute_preferences.map(
            (computePreference) => computePreference.compute_resource_id,
          )
        : [];
      return currentPrefs;
    },
    title: function () {
      return this.id
        ? this.data.group_resource_profile_name
        : "New Group Resource Profile";
    },
    owner() {
      return this.sharedEntity && this.sharedEntity.owner
        ? this.sharedEntity.owner
        : null;
    },
    ownerUserId() {
      return this.owner ? this.owner.user_id : null;
    },
    ownerTitle() {
      return this.owner
        ? this.owner.first_name +
            " " +
            this.owner.last_name +
            " (" +
            this.owner.email +
            ")"
        : null;
    },
  },
  methods: {
    sortedItems(items) {
      return items
        .slice()
        .sort((a, b) =>
          (a.compute_resource_id || "")
            .toLowerCase()
            .localeCompare((b.compute_resource_id || "").toLowerCase()),
        );
    },
    saveGroupResourceProfile: function () {
      let persist;
      if (this.id) {
        persist = this.service.update({ data: this.data, lookup: this.id });
      } else {
        persist = this.service.create({ data: this.data }).then((data) => {
          // Merge sharing settings with default sharing settings created when
          // Group Resource Profile was created
          const groupResourceProfileId = data.group_resource_profile_id;
          return this.$refs.shareButton.mergeAndSave(groupResourceProfileId);
        });
      }
      persist.then(() => {
        this.$router.push("/group-resource-profiles");
      });
    },
    cancel: function () {
      this.$router.push("/group-resource-profiles");
    },
    createComputePreference: function () {
      this.$refs.modalSelectComputeResource.show();
    },
    onSelectComputeResource: function (computeResourceId) {
      const computeResourcePreference =
        new models.GroupComputeResourcePreference();
      computeResourcePreference.compute_resource_id = computeResourceId;
      this.$router.push({
        name: "compute_preference_for_new_group_resource_profile",
        params: {
          value: computeResourcePreference,
          id: this.id,
          host_id: computeResourcePreference.compute_resource_id,
          groupResourceProfile: this.data,
        },
      });
    },
    removeComputePreference: function (computeResourceId) {
      let groupResourceProfile = this.data.clone();
      groupResourceProfile.removeComputeResource(computeResourceId);
      this.service
        .update({ data: groupResourceProfile, lookup: this.id })
        .then((groupResourceProfile) => (this.data = groupResourceProfile));
    },
    removeGroupResourceProfile: function () {
      if (this.id) {
        this.service.delete({ lookup: this.id }).then(() => {
          this.$router.push("/group-resource-profiles");
        });
      } else {
        // Nothing to delete so just treat like a cancel
        this.cancel();
      }
    },
  },
};
</script>
