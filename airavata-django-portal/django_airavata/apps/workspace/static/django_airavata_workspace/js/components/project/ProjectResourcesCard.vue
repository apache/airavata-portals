<template>
  <div class="card mb-3">
    <div class="card-body">
      <div class="d-flex align-items-center mb-3">
        <h5 class="mb-0 me-auto">Resources</h5>
        <button class="btn btn-primary btn-sm" v-if="canEdit && !editing" @click="edit">
          <i class="fa fa-edit me-1"></i>Edit
        </button>
      </div>
      <div v-if="loading" class="text-muted">Loading resource profile...</div>
      <div v-else>
        <div class="small text-muted mb-2">
          Default credential token:
          <code>{{ profile.default_credential_store_token || '—' }}</code>
        </div>
        <div class="small text-muted mb-2" v-if="profile.project_resource_profile_name">
          Profile name:
          <code>{{ profile.project_resource_profile_name }}</code>
        </div>
        <div v-if="editing" class="mt-3">
          <label class="form-label">Default credential token</label>
          <input v-model="draft.default_credential_store_token" class="form-control form-control-sm" placeholder="Credential token" />
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

<script>
import { services, session } from "django-airavata-api";

export default {
  name: "project-resources-card",
  props: { project: { type: Object, required: true } },
  data() {
    return { loading: true, profile: { default_credential_store_token: "" }, editing: false, draft: {}, saving: false };
  },
  computed: {
    currentUser() {
      return session.Session.username;
    },
    canEdit() {
      if (!this.project) return false;
      if (this.project.owner === this.currentUser) return true;
      const admins = this.project.admins || [];
      return admins.includes(this.currentUser);
    },
  },
  created() { this.reload(); },
  methods: {
    async reload() {
      this.loading = true;
      try {
        this.profile = await services.ProjectService.resourceProfile({ lookup: this.project.project_id });
      } catch (e) {
        this.profile = { default_credential_store_token: "" };
      } finally {
        this.loading = false;
      }
    },
    edit() {
      this.draft = { ...this.profile };
      this.editing = true;
    },
    cancel() {
      this.draft = {};
      this.editing = false;
    },
    async save() {
      this.saving = true;
      try {
        await services.ProjectService.updateResourceProfile({
          lookup: this.project.project_id,
          data: this.draft,
        });
        this.editing = false;
        await this.reload();
      } catch (e) {
        window.alert(e?.message || "Failed to save resource profile.");
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>
