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

<script>
import { services, session } from "django-airavata-api";

export default {
  name: "ProjectMembersCard",
  props: { project: { type: Object, required: true } },
  data() {
    return { loading: true, admins: [], members: [], showAdd: false, newUserName: "" };
  },
  computed: {
    currentUser() {
      return session.Session.username;
    },
    canManage() {
      const u = this.currentUser;
      return this.project.owner === u || this.admins.includes(u);
    },
    memberOnly() {
      return this.members.filter((u) => !this.admins.includes(u));
    },
  },
  created() {
    this.reload();
  },
  methods: {
    async reload() {
      this.loading = true;
      try {
        const resp = await services.ProjectService.members({ lookup: this.project.project_id });
        this.admins = resp.admins || [];
        this.members = resp.members || [];
      } catch (e) {
        console.error("Failed to load project members:", e);
        this.admins = [];
        this.members = [];
      } finally {
        this.loading = false;
      }
    },
    async add() {
      try {
        await services.ProjectService.addMember({
          lookup: this.project.project_id,
          data: { user_name: this.newUserName },
        });
        this.newUserName = "";
        this.showAdd = false;
        await this.reload();
      } catch (e) {
        window.alert(e?.message || "Failed to add member.");
      }
    },
    async remove(user) {
      if (!confirm(`Remove ${user} from this project?`)) return;
      try {
        await services.ProjectService.removeMember({
          lookup: this.project.project_id,
          user_name: user,
        });
        await this.reload();
      } catch (e) {
        window.alert(e?.message || "Failed to remove member.");
      }
    },
    async promote(user) {
      try {
        await services.ProjectService.addAdmin({
          lookup: this.project.project_id,
          data: { user_name: user },
        });
        await this.reload();
      } catch (e) {
        window.alert(e?.message || "Failed to promote.");
      }
    },
    async demote(user) {
      try {
        await services.ProjectService.removeAdmin({
          lookup: this.project.project_id,
          user_name: user,
        });
        await this.reload();
      } catch (e) {
        window.alert(e?.message || "Failed to demote.");
      }
    },
  },
};
</script>
