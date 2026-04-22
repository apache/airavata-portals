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
            <table class="table">
              <thead>
                <tr>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Enabled</th>
                  <th>Email Verified</th>
                  <th>Created</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in items" :key="item.airavata_internal_user_id">
                  <td>{{ item.firstName }}</td>
                  <td>{{ item.lastName }}</td>
                  <td>{{ item.userId }}</td>
                  <td>{{ item.email }}</td>
                  <td>{{ item.enabled }}</td>
                  <td>{{ item.emailVerified }}</td>
                  <td>{{ item.creation_time }}</td>
                  <td>
                    <button
                      v-if="item.user_has_write_access"
                      class="btn"
                      @click="toggleDetails(item)"
                    >
                      Edit
                    </button>
                    <div v-if="item._showDetails">
                      <user-details-container
                        :iam-user-profile="item"
                        @enable-user="enableUser"
                        @delete-user="deleteUser"
                        @update-username="updateUsername(item, $event[0], $event[1])"
                      />
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <pager :paginator="usersPaginator" @next="next" @previous="previous"></pager>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { services } from "django-airavata-api";
import UserDetailsContainer from "./UserDetailsContainer.vue";

type IAMUserItem = {
  airavata_internal_user_id: string;
  firstName?: string;
  lastName?: string;
  userId?: string;
  email?: string;
  enabled?: boolean;
  emailVerified?: boolean;
  creation_time?: unknown;
  user_has_write_access?: boolean;
  user_id?: string;
  _showDetails?: boolean;
  newUsername?: string;
  clone: () => IAMUserItem;
  [key: string]: unknown;
};

const usersPaginator = ref<{ results: IAMUserItem[]; offset: number; next: () => void; previous: () => void } | null>(null);
const showingDetails = ref<Record<string, boolean>>({});
const search = ref<string | null>(null);

const currentOffset = computed(() => usersPaginator.value?.offset ?? 0);

const items = computed((): IAMUserItem[] =>
  usersPaginator.value
    ? usersPaginator.value.results.map((u) => {
        const user = u.clone();
        user._showDetails = showingDetails.value[u.airavata_internal_user_id] || false;
        return user;
      })
    : []
);

onMounted(() => {
  services.IAMUserProfileService.list({ limit: 10 }).then(
    (users: typeof usersPaginator.value) => (usersPaginator.value = users)
  );
});

function next() {
  usersPaginator.value!.next();
}

function previous() {
  usersPaginator.value!.previous();
}

function reloadUserProfiles() {
  const params: Record<string, unknown> = {
    limit: 10,
    offset: currentOffset.value,
  };
  if (search.value) {
    params["search"] = search.value;
  }
  services.IAMUserProfileService.list(params).then(
    (users: typeof usersPaginator.value) => (usersPaginator.value = users)
  );
}

function toggleDetails(item: IAMUserItem) {
  showingDetails.value[item.airavata_internal_user_id] =
    !showingDetails.value[item.airavata_internal_user_id];
}

function searchUsers() {
  usersPaginator.value = null;
  reloadUserProfiles();
}

function resetSearch() {
  usersPaginator.value = null;
  search.value = null;
  reloadUserProfiles();
}

function enableUser(username: string) {
  services.IAMUserProfileService.enable({ lookup: username }).finally(() => reloadUserProfiles());
}

function deleteUser(username: string) {
  services.IAMUserProfileService.delete({ lookup: username }).finally(() => reloadUserProfiles());
}

function updateUsername(userProfile: IAMUserItem, _username: string, newUsername: string) {
  const updatedUserProfile = userProfile.clone();
  updatedUserProfile.newUsername = newUsername;
  services.IAMUserProfileService.updateUsername({ data: updatedUserProfile }).finally(() =>
    reloadUserProfiles()
  );
}
</script>
