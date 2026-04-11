<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Group Resource Profiles</h1>
        <p class="text-muted mb-0">Manage compute resource access policies for user groups.</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary btn-sm" @click="newGroupResourcePreference">
          <i class="fa fa-plus me-1"></i>Create New
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="groupResourceProfiles.length === 0">
              <td colspan="3">
                <div class="table-empty">
                  <i class="fa fa-server table-empty__icon"></i>
                  <div class="table-empty__title">No group resource profiles</div>
                  <div class="table-empty__text">Create a profile to configure compute resource access for user groups.</div>
                </div>
              </td>
            </tr>
            <tr v-for="profile in groupResourceProfiles" :key="profile.group_resource_profile_id">
              <td>{{ profile.group_resource_profile_name }}</td>
              <td><human-date :date="profile.updated_time" /></td>
              <td>
                <router-link class="action-link me-2" v-if="profile.user_has_write_access"
                  :to="{ name: 'group_resource_preference', params: { value: profile, id: profile.group_resource_profile_id } }">
                  Edit <i class="fa fa-edit"></i>
                </router-link>
                <router-link class="action-link me-2" v-else
                  :to="{ name: 'group_resource_preference', params: { value: profile, id: profile.group_resource_profile_id } }">
                  View <i class="fa fa-eye"></i>
                </router-link>
                <delete-link v-if="profile.user_has_write_access" class="action-link" @delete="removeGroupResourceProfile(profile)">
                  Are you sure you want to delete <strong>{{ profile.group_resource_profile_name }}</strong>?
                </delete-link>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="groupResourceProfiles.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ groupResourceProfiles.length }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { components } from "django-airavata-common-ui";
import { services } from "django-airavata-api";

export default {
  name: "compute-resource-preference",
  components: {
    "delete-link": components.DeleteLink,
    "human-date": components.HumanDate,
  },
  data() {
    return {
      groupResourceProfiles: [],
    };
  },
  methods: {
    newGroupResourcePreference() {
      this.$router.push({ name: "new_group_resource_preference" });
    },
    loadGroupResourceProfiles() {
      services.GroupResourceProfileService.list().then(
        (profiles) => (this.groupResourceProfiles = profiles)
      );
    },
    removeGroupResourceProfile(profile) {
      services.GroupResourceProfileService.delete({ lookup: profile.group_resource_profile_id })
        .then(() => services.GroupResourceProfileService.list())
        .then((profiles) => (this.groupResourceProfiles = profiles));
    },
  },
  mounted() {
    this.loadGroupResourceProfiles();
  },
};
</script>
