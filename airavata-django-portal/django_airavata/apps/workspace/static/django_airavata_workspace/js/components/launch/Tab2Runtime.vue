<template>
  <div v-if="store.profile">
    <RuntimeInputs
      :profile="store.profile"
      :model-value="store.draft.runtime"
      @update:model-value="store.setRuntime($event)"
    />
    <p class="small text-muted mt-2">
      Allocation <code>{{ store.profile.allocation_id }}</code> (auto from project) ·
      <span v-if="pickedCR">
        Resource <code>{{ pickedCR.compute_resource_id }}</code> ·
        Compute storage <code>{{ pickedCR.mapped_storage.storage_id }}</code>
        scratch <code>{{ pickedCR.mapped_storage.scratch_path }}</code>
      </span>
    </p>
  </div>
  <div v-else class="text-muted">Loading resource profile…</div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import { launcherService } from "django-airavata-common-ui/js/services/launcherService";
import RuntimeInputs from "./runtime/RuntimeInputs.vue";

const store = useLaunchStore();

async function refetch(projectId: string) {
  const p = await launcherService.getProjectResourceProfile(projectId);
  store.setProfile(p);
}

onMounted(() => {
  if (store.draft.project_id) void refetch(store.draft.project_id);
});

watch(
  () => store.draft.project_id,
  (id) => { if (id) void refetch(id); else store.setProfile(null); },
);

const pickedCR = computed(() =>
  store.profile?.compute_resources.find((c) => c.compute_resource_id === store.draft.runtime.compute_resource_id) ?? null,
);
</script>
