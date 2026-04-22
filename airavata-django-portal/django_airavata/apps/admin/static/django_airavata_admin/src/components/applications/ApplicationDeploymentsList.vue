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
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Compute Resource</th>
              <th>Description</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in slotProps.items" :key="item.computeHostId">
              <td>{{ getComputeResourceName(item.computeHostId) }}</td>
              <td>{{ item.appDeploymentDescription }}</td>
              <td>
                <router-link
                  v-if="!item.user_has_write_access"
                  class="action-link"
                  :to="{
                    name: 'application_deployment',
                    params: {
                      id: id,
                      deploymentId: item.appDeploymentId,
                    },
                    query: { readonly: 'true' },
                  }"
                >
                  View
                  <i class="fa fa-eye" aria-hidden="true"></i>
                </router-link>
                <router-link
                  v-if="item.user_has_write_access && item.appDeploymentId"
                  class="action-link"
                  :to="{
                    name: 'application_deployment',
                    params: {
                      id: id,
                      deploymentId: item.appDeploymentId,
                    },
                  }"
                >
                  Edit
                  <i class="fa fa-edit" aria-hidden="true"></i>
                </router-link>
                <router-link
                  v-if="item.user_has_write_access && !item.appDeploymentId"
                  class="action-link"
                  :to="{
                    name: 'new_application_deployment',
                    params: {
                      id: id,
                      hostId: item.computeHostId,
                    },
                  }"
                >
                  Edit
                  <i class="fa fa-edit" aria-hidden="true"></i>
                </router-link>
                <delete-link
                  v-if="item.user_has_write_access"
                  class="action-link"
                  @delete="removeApplicationDeployment(item)"
                >
                  Are you sure you want to remove the
                  <strong>{{ getComputeResourceName(item.computeHostId) }}</strong>
                  deployment?
                </delete-link>
              </td>
            </tr>
          </tbody>
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

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { services } from "django-airavata-api";
import { components, layouts } from "django-airavata-common-ui";
import ComputeResourcesModal from "../admin/ComputeResourcesModal.vue";

const ListLayout = layouts.ListLayout;
const DeleteLink = components.DeleteLink;

interface Deployment {
  computeHostId: string;
  appDeploymentId?: string;
  appDeploymentDescription?: string;
  user_has_write_access?: boolean;
  compute_host_id?: string;
}

const props = defineProps<{
  deployments: Deployment[];
  id: string;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  new: [computeResourceId: string];
  delete: [deployment: Deployment];
}>();

const modalSelectComputeResource = ref<InstanceType<typeof ComputeResourcesModal> | null>(null);
const computeResourceNames = ref<Record<string, string> | null>(null);

const selectableComputeResourceNames = computed(() => {
  if (!computeResourceNames.value) return [];
  const result: Array<{ host_id: string; host: string }> = [];
  for (const computeResourceId in computeResourceNames.value) {
    if (Object.prototype.hasOwnProperty.call(computeResourceNames.value, computeResourceId)) {
      result.push({
        host_id: computeResourceId,
        host: computeResourceNames.value[computeResourceId],
      });
    }
  }
  return result;
});

const excludedComputeResourceIds = computed(() =>
  props.deployments.map((dep) => dep.computeHostId),
);

onMounted(() => {
  services.ComputeResourceService.names().then(
    (names: Record<string, string>) => (computeResourceNames.value = names),
  );
});

function getComputeResourceName(computeResourceId: string) {
  if (computeResourceNames.value && computeResourceId in computeResourceNames.value) {
    return computeResourceNames.value[computeResourceId];
  } else {
    return computeResourceId.substring(0, 10) + "...";
  }
}

function onSelectComputeResource(computeResourceId: string | null) {
  if (computeResourceId) {
    emit("new", computeResourceId);
  }
}

function newApplicationDeployment() {
  modalSelectComputeResource.value?.show();
}

function removeApplicationDeployment(deployment: Deployment) {
  emit("delete", deployment);
}
</script>
