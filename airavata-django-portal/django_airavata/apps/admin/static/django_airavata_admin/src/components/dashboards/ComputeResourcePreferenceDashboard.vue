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
            <tr v-for="profile in groupResourceProfiles" :key="profile.groupResourceProfileId">
              <td>{{ profile.groupResourceProfileName }}</td>
              <td><human-date :date="profile.updatedTime" /></td>
              <td>
                <router-link class="action-link me-2" v-if="profile.userHasWriteAccess"
                  :to="{ name: 'group_resource_preference', params: { value: profile, id: profile.groupResourceProfileId } }">
                  Edit <i class="fa fa-edit"></i>
                </router-link>
                <router-link class="action-link me-2" v-else
                  :to="{ name: 'group_resource_preference', params: { value: profile, id: profile.groupResourceProfileId } }">
                  View <i class="fa fa-eye"></i>
                </router-link>
                <delete-link v-if="profile.userHasWriteAccess" class="action-link" @delete="removeGroupResourceProfile(profile)">
                  Are you sure you want to delete <strong>{{ profile.groupResourceProfileName }}</strong>?
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
      services.GroupResourceProfileService.delete({ lookup: profile.groupResourceProfileId })
        .then(() => services.GroupResourceProfileService.list())
        .then((profiles) => (this.groupResourceProfiles = profiles));
    },
  },
  mounted() {
    this.loadGroupResourceProfiles();
  },
};
</script>
