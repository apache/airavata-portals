<template>
  <div>
    <list-layout
      :items="deployments"
      title="Application Deployments"
      new-item-button-text="New Deployment"
      :new-button-disabled="readonly"
      @add-new-item="newApplicationDeployment"
    >
      <template #item-list="slotProps">
        <!-- TODO: migrate to native HTML table -->
        <table
          class="table"
          striped
          hover
          :fields="fields"
          :items="slotProps.items"
          sort-by="computeHostId"
        >
          <template slot="cell(action)" slot-scope="data">
            <router-link
              v-if="!data.item.user_has_write_access"
              class="action-link"
              :to="{
                name: 'application_deployment',
                params: {
                  id: id,
                  deploymentId: data.item.appDeploymentId,
                  readonly: true,
                },
              }"
            >
              View
              <i class="fa fa-eye" aria-hidden="true"></i>
            </router-link>
            <router-link
              v-if="data.item.user_has_write_access && data.item.appDeploymentId"
              class="action-link"
              :to="{
                name: 'application_deployment',
                params: {
                  id: id,
                  deploymentId: data.item.appDeploymentId,
                  readonly: false,
                },
              }"
            >
              Edit
              <i class="fa fa-edit" aria-hidden="true"></i>
            </router-link>
            <router-link
              v-if="data.item.user_has_write_access && !data.item.appDeploymentId"
              class="action-link"
              :to="{
                name: 'new_application_deployment',
                params: {
                  id: id,
                  hostId: data.item.computeHostId,
                  readonly: false,
                },
              }"
            >
              Edit
              <i class="fa fa-edit" aria-hidden="true"></i>
            </router-link>
            <delete-link
              v-if="data.item.user_has_write_access"
              class="action-link"
              @delete="removeApplicationDeployment(data.item)"
            >
              Are you sure you want to remove the
              <strong>{{ getComputeResourceName(data.item.computeHostId) }}</strong>
              deployment?
            </delete-link>
          </template>
        </table>
      </template>
    </list-layout>
    <compute-resources-modal
      ref="modalSelectComputeResource"
      :compute-resource-names="selectableComputeResourceNames"
      :excluded-resource-ids="excludedComputeResourceIds"
      @selected="onSelectComputeResource"
    />
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { components, layouts } from "django-airavata-common-ui";
import ComputeResourcesModal from "../admin/ComputeResourcesModal.vue";

export default {
  name: "ApplicationDeploymentsList",
  components: {
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
    };
  },
  computed: {
    fields() {
      return [
        {
          label: "Compute Resource",
          key: "computeHostId",
          sortable: true,
          formatter: (value) => this.getComputeResourceName(value),
        },
        {
          label: "Description",
          key: "appDeploymentDescription",
        },
        {
          label: "Action",
          key: "action",
        },
      ];
    },
    selectableComputeResourceNames() {
      if (!this.computeResourceNames) return [];
      const result = [];
      for (const computeResourceId in this.computeResourceNames) {
        if (Object.prototype.hasOwnProperty.call(this.computeResourceNames, computeResourceId)) {
          result.push({
            host_id: computeResourceId,
            host: this.computeResourceNames[computeResourceId],
          });
        }
      }
      return result;
    },
    excludedComputeResourceIds() {
      return this.deployments.map((dep) => dep.computeHostId);
    },
  },
  mounted() {
    services.ComputeResourceService.names().then((names) => (this.computeResourceNames = names));
  },
  methods: {
    getComputeResourceName(computeResourceId) {
      if (this.computeResourceNames && computeResourceId in this.computeResourceNames) {
        return this.computeResourceNames[computeResourceId];
      } else {
        return computeResourceId.substring(0, 10) + "...";
      }
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
