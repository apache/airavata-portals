<template>
  <div class="space-y-4">
    <Card>
      <CardContent>
        <div class="flex items-stretch gap-2">
          <Input
            v-model="search"
            placeholder="Search by name, email or username"
            @keydown.enter="searchUsers"
          />
          <Button variant="outline" @click="resetSearch">Reset</Button>
          <Button variant="default" @click="searchUsers">Search</Button>
        </div>
      </CardContent>
    </Card>
    <Card>
      <CardContent>
        <Table class="table-fixed">
          <TableHeader>
            <TableRow>
              <TableHead v-for="field in fields" :key="field.key">
                {{ field.label }}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <template
              v-for="item in items"
              :key="item.airavata_internal_user_id"
            >
              <TableRow>
                <TableCell>{{ item.first_name }}</TableCell>
                <TableCell>{{ item.last_name }}</TableCell>
                <TableCell>{{ item.user_id }}</TableCell>
                <TableCell>{{ item.email }}</TableCell>
                <TableCell>{{ item.enabled }}</TableCell>
                <TableCell>{{ item.email_verified }}</TableCell>
                <TableCell>
                  <group-membership-display :groups="item.groups" />
                </TableCell>
                <TableCell><human-date :date="item.creation_time" /></TableCell>
                <TableCell>
                  <Button
                    v-if="item.user_has_write_access"
                    variant="outline"
                    @click="toggleDetails(item)"
                  >
                    Edit
                  </Button>
                </TableCell>
              </TableRow>
              <TableRow v-if="item._showDetails">
                <TableCell :colspan="fields.length">
                  <user-details-container
                    :iam-user-profile="item"
                    :editable-groups="editableGroups"
                    @groups-updated="groupsUpdated"
                    @enable-user="enableUser"
                    @delete-user="deleteUser"
                    @update-username="updateUsername(item, ...$event)"
                  />
                </TableCell>
              </TableRow>
            </template>
          </TableBody>
        </Table>
        <pager
          v-bind:paginator="usersPaginator"
          v-on:next="next"
          v-on:previous="previous"
        ></pager>
      </CardContent>
    </Card>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import UserDetailsContainer from "./UserDetailsContainer.vue";
import GroupMembershipDisplay from "./GroupMembershipDisplay";

export default {
  name: "user-management-container",
  data() {
    return {
      usersPaginator: null,
      allGroups: null,
      showingDetails: {},
      search: null,
    };
  },
  components: {
    pager: components.Pager,
    "human-date": components.HumanDate,
    UserDetailsContainer,
    GroupMembershipDisplay,
  },
  created() {
    services.IAMUserProfileService.list({ limit: 10 }).then(
      (users) => (this.usersPaginator = users),
    );
    services.GroupService.list({ limit: -1 }).then(
      (groups) => (this.allGroups = groups),
    );
  },
  computed: {
    fields() {
      return [
        {
          label: "First Name",
          key: "first_name",
        },
        {
          label: "Last Name",
          key: "last_name",
        },
        {
          label: "Username",
          key: "user_id",
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
          key: "email_verified",
        },
        {
          label: "Groups",
          key: "groups",
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
            user._showDetails =
              this.showingDetails[u.airavata_internal_user_id] || false;
            return user;
          })
        : [];
    },
    editableGroups() {
      return this.allGroups
        ? this.allGroups.filter((g) => g.is_admin || g.is_owner)
        : [];
    },
    currentOffset() {
      return this.usersPaginator ? this.usersPaginator.offset : 0;
    },
  },
  methods: {
    next() {
      this.usersPaginator.next();
    },
    previous() {
      this.usersPaginator.previous();
    },
    groupsUpdated(user) {
      services.IAMUserProfileService.update({
        lookup: user.user_id,
        data: user,
      }).finally(() => {
        this.reloadUserProfiles();
      });
    },
    reloadUserProfiles() {
      const params = {
        limit: 10,
        offset: this.currentOffset,
      };
      if (this.search) {
        params["search"] = this.search;
      }
      services.IAMUserProfileService.list(params).then(
        (users) => (this.usersPaginator = users),
      );
    },
    toggleDetails(item) {
      this.showingDetails[item.airavata_internal_user_id] =
        !this.showingDetails[item.airavata_internal_user_id];
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
