<template>
  <tr style="cursor: pointer" @click="navigate">
    <td>
      <i class="fa fa-folder me-2 text-muted"></i>
      <strong>{{ project.name }}</strong>
    </td>
    <td>
      <span class="fw-medium">{{ ownerUsername }}</span>
      <span v-if="isCurrentUser" class="badge bg-secondary ms-1">You</span>
      <span v-else-if="isAdmin" class="badge bg-primary ms-1">Admin</span>
    </td>
    <td class="text-nowrap" :title="project.creation_time != null ? String(project.creation_time) : undefined">{{ creationTime }}</td>
    <td class="text-nowrap" style="width: 1%" @click.stop>
      <div class="d-flex gap-2 justify-content-end flex-nowrap">
        <button
          type="button"
          class="btn btn-outline-danger btn-pill"
          @click="$emit('delete', project)"
        >
          <i class="fa fa-trash me-1" aria-hidden="true"></i>Delete
        </button>
      </div>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { computed } from "vue";
import urls from "../../utils/urls";
import { relativeTime } from "django-airavata-common-ui/js/utils/dates";
import { session } from "django-airavata-api";

interface Project {
  project_id: string;
  name: string;
  owner?: string;
  creation_time?: string | Date;
  [key: string]: unknown;
}

const props = defineProps<{
  project: Project;
}>();

defineEmits<{
  delete: [project: Project];
}>();

const creationTime = computed(() => {
  const dt = new Date(props.project.creation_time as string);
  return relativeTime(dt);
});

const overviewLink = computed(() => urls.projectOverview(props.project));

const ownerUsername = computed(() => {
  const owner = (props.project.owner as string) || "";
  const lastAt = owner.lastIndexOf("@");
  return lastAt > 0 ? owner.substring(0, lastAt) : owner;
});

const isCurrentUser = computed(() => ownerUsername.value === session.Session.username);

const isAdmin = computed(() => {
  const name = ownerUsername.value;
  return name === "default-admin" || name === "admin";
});

function navigate() {
  window.location.href = overviewLink.value;
}
</script>
