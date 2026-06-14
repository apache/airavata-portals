<template>
  <div>
    <list-layout
      @add-new-item="newApplicationDeployment"
      :items="deployments"
      title="Application Deployments"
      new-item-button-text="New Deployment"
      :new-button-disabled="readonly"
    >
      <template v-slot:item-list="slotProps">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead v-for="field in fields" :key="field.key">
                {{ field.label }}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="item in sortedItems(slotProps.items)"
              :key="item.compute_host_id"
            >
              <TableCell>{{
                getComputeResourceName(item.compute_host_id)
              }}</TableCell>
              <TableCell>{{ item.app_deployment_description }}</TableCell>
              <TableCell>
                <router-link
                  class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                  v-if="!item.user_has_write_access"
                  :to="{
                    name: 'application_deployment',
                    params: {
                      id: id,
                      deploymentId: item.app_deployment_id,
                      readonly: true,
                    },
                  }"
                >
                  View
                  <Eye class="size-4" aria-hidden="true" />
                </router-link>
                <router-link
                  class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                  v-if="item.user_has_write_access && item.app_deployment_id"
                  :to="{
                    name: 'application_deployment',
                    params: {
                      id: id,
                      deploymentId: item.app_deployment_id,
                      readonly: false,
                    },
                  }"
                >
                  Edit
                  <Pencil class="size-4" aria-hidden="true" />
                </router-link>
                <router-link
                  class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                  v-if="item.user_has_write_access && !item.app_deployment_id"
                  :to="{
                    name: 'new_application_deployment',
                    params: {
                      id: id,
                      hostId: item.compute_host_id,
                      readonly: false,
                    },
                  }"
                >
                  Edit
                  <Pencil class="size-4" aria-hidden="true" />
                </router-link>
                <delete-link
                  v-if="item.user_has_write_access"
                  @delete="removeApplicationDeployment(item)"
                >
                  Are you sure you want to remove the
                  <strong>{{
                    getComputeResourceName(item.compute_host_id)
                  }}</strong>
                  deployment?
                </delete-link>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </template>
    </list-layout>
    <compute-resources-modal
      ref="modalSelectComputeResource"
      @selected="onSelectComputeResource"
      :compute-resource-names="selectableComputeResourceNames"
      :excluded-resource-ids="excludedComputeResourceIds"
    />
  </div>
</template>

<script>
import { Eye, Pencil } from "@lucide/vue";
import { services } from "django-airavata-api";
import { components, layouts } from "django-airavata-common-ui";
import ComputeResourcesModal from "../admin/ComputeResourcesModal.vue";

export default {
  name: "application-deployments-list",
  components: {
    Eye,
    Pencil,
    "list-layout": layouts.ListLayout,
    ComputeResourcesModal,
    "delete-link": components.DeleteLink,
  },
  props: {
    deployments: {
      type: Array,
      required: true,
    },
    id: {
      // app module id
      type: String,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      computeResourceNames: null,
      groupResourceProfiles: null,
    };
  },
  computed: {
    fields() {
      return [
        {
          label: "Compute Resource",
          key: "compute_host_id",
          sortable: true,
          formatter: (value) => this.getComputeResourceName(value),
        },
        {
          label: "Description",
          key: "app_deployment_description",
        },
        {
          label: "Action",
          key: "action",
        },
      ];
    },
    selectableComputeResourceNames() {
      // Only allow selecting a compute resource for a new deployment if that
      // compute resource exists in a GroupResourceProfile
      if (this.computeResourceNames && this.groupResourceProfiles) {
        // Create a set of all computeResourceIds in GroupResourceProfiles
        const groupResourceProfileCompResources = {};
        for (const groupResourceProfile of this.groupResourceProfiles) {
          for (const computePreference of groupResourceProfile.compute_preferences) {
            groupResourceProfileCompResources[
              computePreference.compute_resource_id
            ] = null;
          }
        }
        const result = [];
        // Filter compute resources based on existence in groupResourceProfileCompResources
        for (const computeResourceId in this.computeResourceNames) {
          if (
            Object.prototype.hasOwnProperty.call(
              this.computeResourceNames,
              computeResourceId,
            ) &&
            Object.prototype.hasOwnProperty.call(
              groupResourceProfileCompResources,
              computeResourceId,
            )
          ) {
            const computeResourceName =
              this.computeResourceNames[computeResourceId];
            result.push({
              host_id: computeResourceId,
              host: computeResourceName,
            });
          }
        }
        return result;
      } else {
        return [];
      }
    },
    excludedComputeResourceIds() {
      return this.deployments.map((dep) => dep.compute_host_id);
    },
  },
  mounted() {
    services.ComputeResourceService.names().then(
      (names) => (this.computeResourceNames = names),
    );
    services.GroupResourceProfileService.list().then(
      (groupResourceProfiles) =>
        (this.groupResourceProfiles = groupResourceProfiles),
    );
  },
  methods: {
    getComputeResourceName(computeResourceId) {
      if (
        this.computeResourceNames &&
        computeResourceId in this.computeResourceNames
      ) {
        return this.computeResourceNames[computeResourceId];
      } else {
        return computeResourceId.substring(0, 10) + "...";
      }
    },
    sortedItems(items) {
      return items
        .slice()
        .sort((a, b) =>
          this.getComputeResourceName(a.compute_host_id)
            .toLowerCase()
            .localeCompare(
              this.getComputeResourceName(b.compute_host_id).toLowerCase(),
            ),
        );
    },
    onSelectComputeResource(computeResourceId) {
      this.$emit("new", computeResourceId);
    },
    newApplicationDeployment() {
      this.$refs.modalSelectComputeResource.show();
    },
    removeApplicationDeployment(deployment) {
      this.$emit("delete", deployment);
    },
  },
};
</script>
