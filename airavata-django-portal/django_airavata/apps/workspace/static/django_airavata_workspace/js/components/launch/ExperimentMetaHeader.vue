<template>
  <div class="row g-2 mb-2">
    <div class="col-md-6">
      <input
        data-test="exp-name"
        aria-label="Experiment name"
        class="form-control"
        :value="store.draft.name"
        placeholder="Experiment name"
        maxlength="256"
        @input="onName(($event.target as HTMLInputElement).value)"
      />
    </div>
    <div class="col-md-6">
      <select
        data-test="exp-project"
        aria-label="Project"
        class="form-select"
        :value="store.draft.project_id ?? ''"
        @change="onProject(($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Select a project</option>
        <option v-for="p in projects" :key="p.project_id" :value="p.project_id">
          {{ p.name }}
        </option>
      </select>
    </div>
    <div class="col-12">
      <textarea
        data-test="exp-description"
        aria-label="Description"
        class="form-control"
        rows="2"
        :value="store.draft.description"
        placeholder="Description (optional)"
        @input="onDescription(($event.target as HTMLTextAreaElement).value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import { useConfirmReset } from "../../composables/useConfirmReset";

defineProps<{ projects: Array<{ project_id: string; name: string }> }>();

const store = useLaunchStore();

function onName(v: string) {
  store.setMeta({ name: v, project_id: store.draft.project_id, description: store.draft.description });
}

const guardedProject = useConfirmReset(
  "Switching project clears your runtime selections. Continue?",
  (id: string | null) => {
    store.setMeta({ name: store.draft.name, project_id: id, description: store.draft.description });
  },
);

function onProject(v: string) {
  const next = v || null;
  if (store.draft.project_id && store.draft.project_id !== next) {
    guardedProject(next);
  } else {
    store.setMeta({ name: store.draft.name, project_id: next, description: store.draft.description });
  }
}

function onDescription(v: string) {
  store.setMeta({ name: store.draft.name, project_id: store.draft.project_id, description: v });
}
</script>
