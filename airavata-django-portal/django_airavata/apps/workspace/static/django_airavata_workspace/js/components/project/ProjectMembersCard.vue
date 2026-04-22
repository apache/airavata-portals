<template>
  <div class="card mb-3">
    <div class="card-body">
      <div class="d-flex align-items-center mb-3">
        <h5 class="mb-0 me-auto">Members</h5>
        <button v-if="canManage" class="btn btn-primary btn-sm" @click="showAdd = true">
          <i class="fa fa-plus me-1"></i>Add
        </button>
      </div>
      <div v-if="loading" class="text-muted">Loading members...</div>
      <table v-else class="table table-sm mb-0">
        <tbody>
          <tr v-if="admins.length === 0 && memberOnly.length === 0">
            <td colspan="2" class="text-muted text-center py-2">No members yet.</td>
          </tr>
          <tr v-for="user in admins" :key="'a-' + user">
            <td>
              <i class="fa fa-user me-2 text-muted"></i>
              {{ user }}
              <span class="badge bg-primary ms-1">Admin</span>
              <span v-if="user === project.owner" class="badge bg-secondary ms-1">Owner</span>
            </td>
            <td v-if="canManage && user !== project.owner" class="text-end">
              <button class="btn btn-sm btn-outline-secondary" @click="demote(user)">Demote</button>
              <button class="btn btn-sm btn-outline-danger ms-1" @click="remove(user)">
                Remove
              </button>
            </td>
            <td v-else></td>
          </tr>
          <tr v-for="user in memberOnly" :key="'m-' + user">
            <td>
              <i class="fa fa-user me-2 text-muted"></i>
              {{ user }}
            </td>
            <td v-if="canManage" class="text-end">
              <button class="btn btn-sm btn-outline-secondary" @click="promote(user)">
                Promote
              </button>
              <button class="btn btn-sm btn-outline-danger ms-1" @click="remove(user)">
                Remove
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="showAdd" class="mt-3">
        <div class="input-group input-group-sm">
          <input
            v-model="newUserName"
            class="form-control"
            placeholder="Username (e.g. alice@default)"
          />
          <button class="btn btn-primary" :disabled="!newUserName" @click="add">Add</button>
          <button
            class="btn btn-secondary"
            @click="
              showAdd = false;
              newUserName = '';
            "
          >
            Cancel
          </button>
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
  [key: string]: unknown;
}

const props = defineProps<{
  project: Project;
}>();

const loading = ref(true);
const admins = ref<string[]>([]);
const members = ref<string[]>([]);
const showAdd = ref(false);
const newUserName = ref("");

const currentUser = computed<string>(() => session.Session.username);
const canManage = computed(() => {
  const u = currentUser.value;
  return props.project.owner === u || admins.value.includes(u);
});
const memberOnly = computed(() => members.value.filter((u) => !admins.value.includes(u)));

async function reload() {
  loading.value = true;
  try {
    const resp = await services.ProjectService.members({ lookup: props.project.project_id });
    admins.value = resp.admins || [];
    members.value = resp.members || [];
  } catch (e) {
    console.error("Failed to load project members:", e);
    admins.value = [];
    members.value = [];
  } finally {
    loading.value = false;
  }
}

async function add() {
  try {
    await services.ProjectService.addMember({
      lookup: props.project.project_id,
      data: { user_name: newUserName.value },
    });
    newUserName.value = "";
    showAdd.value = false;
    await reload();
  } catch (e: unknown) {
    window.alert((e as Error)?.message || "Failed to add member.");
  }
}

async function remove(user: string) {
  if (!confirm(`Remove ${user} from this project?`)) return;
  try {
    await services.ProjectService.removeMember({
      lookup: props.project.project_id,
      user_name: user,
    });
    await reload();
  } catch (e: unknown) {
    window.alert((e as Error)?.message || "Failed to remove member.");
  }
}

async function promote(user: string) {
  try {
    await services.ProjectService.addAdmin({
      lookup: props.project.project_id,
      data: { user_name: user },
    });
    await reload();
  } catch (e: unknown) {
    window.alert((e as Error)?.message || "Failed to promote.");
  }
}

async function demote(user: string) {
  try {
    await services.ProjectService.removeAdmin({
      lookup: props.project.project_id,
      data: { user_name: user },
    });
    await reload();
  } catch (e: unknown) {
    window.alert((e as Error)?.message || "Failed to demote.");
  }
}

onMounted(() => {
  reload();
});
</script>
