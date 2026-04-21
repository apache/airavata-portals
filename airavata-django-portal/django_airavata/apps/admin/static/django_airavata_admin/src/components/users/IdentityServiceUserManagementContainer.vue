<template>
  <div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <div class="input-group">
              <input
                v-model="search"
                class="form-control"
                placeholder="Search by name, email or username"
                @keydown.enter="searchUsers"
              />
              <span class="input-group-text">
                <button class="btn" @click="resetSearch">Reset</button>
                <button class="btn btn-primary btn-sm" @click="searchUsers">Search</button>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <!-- TODO: Replace b-table with native table -->
            <table class="table" hover :fields="fields" :items="items" :fixed="true">
              <template slot="cell(creation_time)" slot-scope="data">
                <human-date :date="data.value" />
              </template>
              <template slot="cell(action)" slot-scope="data">
                <button
                  v-if="data.item.user_has_write_access"
                  class="btn"
                  @click="toggleDetails(data)"
                >
                  Edit
                </button>
              </template>
              <template slot="row-details" slot-scope="data">
                <user-details-container
                  :iam-user-profile="data.item"
                  @enable-user="enableUser"
                  @delete-user="deleteUser"
                  @update-username="updateUsername(data.item, ...$event)"
                />
              </template>
            </table>
            <pager :paginator="usersPaginator" @next="next" @previous="previous"></pager>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import UserDetailsContainer from "./UserDetailsContainer.vue";

export default {
  name: "UserManagementContainer",
  components: {
    pager: components.Pager,
    "human-date": components.HumanDate,
    UserDetailsContainer,
  },
  data() {
    return {
      usersPaginator: null,
      showingDetails: {},
      search: null,
    };
  },
  computed: {
    fields() {
      return [
        {
          label: "First Name",
          key: "firstName",
        },
        {
          label: "Last Name",
          key: "lastName",
        },
        {
          label: "Username",
          key: "userId",
        },
        {
          label: "Email",
          key: "email",
        },
        {
          label: "Enabled",
          key: "enabled",
        },
        {
          label: "Email Verified",
          key: "emailVerified",
        },
        {
          label: "Created",
          key: "creation_time",
        },
        {
          label: "Action",
          key: "action",
        },
      ];
    },
    items() {
      return this.usersPaginator
        ? this.usersPaginator.results.map((u) => {
            const user = u.clone();
            user._showDetails = this.showingDetails[u.airavata_internal_user_id] || false;
            return user;
          })
        : [];
    },
    currentOffset() {
      return this.usersPaginator ? this.usersPaginator.offset : 0;
    },
  },
  created() {
    services.IAMUserProfileService.list({ limit: 10 }).then(
      (users) => (this.usersPaginator = users),
    );
  },
  methods: {
    next() {
      this.usersPaginator.next();
    },
    previous() {
      this.usersPaginator.previous();
    },
    reloadUserProfiles() {
      const params = {
        limit: 10,
        offset: this.currentOffset,
      };
      if (this.search) {
        params["search"] = this.search;
      }
      services.IAMUserProfileService.list(params).then((users) => (this.usersPaginator = users));
    },
    toggleDetails(row) {
      row.toggleDetails();
      this.showingDetails[row.item.airavata_internal_user_id] =
        !this.showingDetails[row.item.airavata_internal_user_id];
    },
    searchUsers() {
      // Reset paginator when starting a search
      this.usersPaginator = null;
      this.reloadUserProfiles();
    },
    resetSearch() {
      this.usersPaginator = null;
      this.search = null;
      this.reloadUserProfiles();
    },
    enableUser(username) {
      services.IAMUserProfileService.enable({ lookup: username }).finally(() =>
        this.reloadUserProfiles(),
      );
    },
    deleteUser(username) {
      services.IAMUserProfileService.delete({ lookup: username }).finally(() =>
        this.reloadUserProfiles(),
      );
    },
    updateUsername(userProfile, username, newUsername) {
      const updatedUserProfile = userProfile.clone();
      updatedUserProfile.newUsername = newUsername;
      services.IAMUserProfileService.updateUsername({
        data: updatedUserProfile,
      }).finally(() => this.reloadUserProfiles());
    },
  },
};
</script>
