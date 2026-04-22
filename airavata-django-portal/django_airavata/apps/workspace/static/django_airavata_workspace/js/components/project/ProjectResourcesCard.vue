<template>
  <div class="card mb-3">
    <div class="card-body">
      <div class="d-flex align-items-center mb-3">
        <h5 class="mb-0 me-auto">Resources</h5>
        <button v-if="canEdit && !editing" class="btn btn-primary btn-sm" @click="edit">
          <i class="fa fa-edit me-1"></i>Edit
        </button>
      </div>
      <div v-if="loading" class="text-muted">Loading resource profile...</div>
      <div v-else>
        <div class="small text-muted mb-2">
          Default credential token:
          <code>{{ profile.default_credential_store_token || "—" }}</code>
        </div>
        <div v-if="profile.project_resource_profile_name" class="small text-muted mb-2">
          Profile name:
          <code>{{ profile.project_resource_profile_name }}</code>
        </div>
        <div v-if="editing" class="mt-3">
          <label class="form-label">Default credential token</label>
          <input
            v-model="draft.default_credential_store_token"
            class="form-control form-control-sm"
            placeholder="Credential token"
          />
          <div class="mt-2">
            <button class="btn btn-primary btn-sm me-1" :disabled="saving" @click="save">
              <i v-if="saving" class="fa fa-spinner fa-spin me-1"></i>Save
            </button>
            <button class="btn btn-secondary btn-sm" @click="cancel">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { services, session } from "django-airavata-api";

interface Project {
  project_id: string;
  owner?: string;
  admins?: string[];
  [key: string]: unknown;
}

interface ResourceProfile {
  default_credential_store_token?: string;
  project_resource_profile_name?: string;
  [key: string]: unknown;
}

const props = defineProps<{
  project: Project;
}>();

const loading = ref(true);
const profile = ref<ResourceProfile>({ default_credential_store_token: "" });
const editing = ref(false);
const draft = ref<ResourceProfile>({});
const saving = ref(false);

const currentUser = computed<string>(() => session.Session.username);
const canEdit = computed(() => {
  if (!props.project) return false;
  if (props.project.owner === currentUser.value) return true;
  const projectAdmins = props.project.admins || [];
  return projectAdmins.includes(currentUser.value);
});

async function reload() {
  loading.value = true;
  try {
    profile.value = await services.ProjectService.resourceProfile({
      lookup: props.project.project_id,
    });
  } catch {
    profile.value = { default_credential_store_token: "" };
  } finally {
    loading.value = false;
  }
}

function edit() {
  draft.value = { ...profile.value };
  editing.value = true;
}

function cancel() {
  draft.value = {};
  editing.value = false;
}

async function save() {
  saving.value = true;
  try {
    await services.ProjectService.updateResourceProfile({
      lookup: props.project.project_id,
      data: draft.value,
    });
    editing.value = false;
    await reload();
  } catch (e: unknown) {
    window.alert((e as Error)?.message || "Failed to save resource profile.");
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  reload();
});
</script>
