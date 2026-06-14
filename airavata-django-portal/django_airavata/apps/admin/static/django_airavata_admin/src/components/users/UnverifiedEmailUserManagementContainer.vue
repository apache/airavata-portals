<template>
  <div>
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
            <template v-for="item in items" :key="item.user_id">
              <TableRow>
                <TableCell>{{ item.first_name }}</TableCell>
                <TableCell>{{ item.last_name }}</TableCell>
                <TableCell>{{ item.user_id }}</TableCell>
                <TableCell>{{ item.email }}</TableCell>
                <TableCell>{{ item.email_verified }}</TableCell>
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
              <TableRow v-if="isExpanded(item)">
                <TableCell :colspan="fields.length">
                  <enable-user-panel
                    v-if="!item.enabled && !item.email_verified"
                    :username="item.user_id"
                    :email="item.email"
                    @enable-user="enableUser"
                  />
                  <delete-user-panel
                    v-if="!item.enabled && !item.email_verified"
                    :username="item.user_id"
                    @delete-user="deleteUser"
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
import { components } from "django-airavata-common-ui";
import { services } from "django-airavata-api";
import EnableUserPanel from "./EnableUserPanel";
import DeleteUserPanel from "./DeleteUserPanel";

export default {
  name: "unverified-email-user-management-container",
  data() {
    return {
      usersPaginator: null,
      showingDetails: {},
    };
  },
  components: {
    pager: components.Pager,
    "human-date": components.HumanDate,
    EnableUserPanel,
    DeleteUserPanel,
  },
  created() {
    services.UnverifiedEmailUserProfileService.list({ limit: 10 }).then(
      (users) => (this.usersPaginator = users),
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
          label: "Email Verified",
          key: "email_verified",
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
      return this.usersPaginator ? this.usersPaginator.results : [];
    },
  },
  methods: {
    next() {
      this.usersPaginator.next();
    },
    previous() {
      this.usersPaginator.previous();
    },
    enableUser(username) {
      services.IAMUserProfileService.enable({ lookup: username }).finally(() =>
        this.loadUnverifiedEmailUsers(),
      );
    },
    deleteUser(username) {
      services.IAMUserProfileService.delete({ lookup: username }).finally(() =>
        this.loadUnverifiedEmailUsers(),
      );
    },
    loadUnverifiedEmailUsers() {
      return services.UnverifiedEmailUserProfileService.list({
        limit: 10,
      }).then((users) => (this.usersPaginator = users));
    },
    isExpanded(item) {
      return Boolean(this.showingDetails[item.user_id]);
    },
    toggleDetails(item) {
      this.showingDetails[item.user_id] = !this.showingDetails[item.user_id];
    },
  },
};
</script>
