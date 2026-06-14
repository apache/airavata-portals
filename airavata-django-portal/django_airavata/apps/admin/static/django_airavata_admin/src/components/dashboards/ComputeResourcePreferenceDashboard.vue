<template>
  <main-layout
    title="Group Resource Profiles"
    subtitle="Manage compute resource access and preferences for groups."
  >
    <template v-slot:actions>
      <Button @click="newGroupResourcePreference">
        New Group Resource Profile
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </template>
    <Card>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead v-for="field in fields" :key="field.key">
                {{ field.label }}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="item in groupResourceProfiles"
              :key="item.group_resource_profile_id"
            >
              <TableCell>{{ item.group_resource_profile_name }}</TableCell>
              <TableCell><human-date :date="item.updated_time" /></TableCell>
              <TableCell>
                <router-link
                  class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                  v-if="item.user_has_write_access"
                  :to="{
                    name: 'group_resource_preference',
                    params: {
                      value: item,
                      id: item.group_resource_profile_id,
                    },
                  }"
                >
                  Edit
                  <Pencil class="size-4" aria-hidden="true" />
                </router-link>
                <router-link
                  class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                  v-if="!item.user_has_write_access"
                  :to="{
                    name: 'group_resource_preference',
                    params: {
                      value: item,
                      id: item.group_resource_profile_id,
                    },
                  }"
                >
                  View
                  <Eye class="size-4" aria-hidden="true" />
                </router-link>
                <delete-link
                  v-if="item.user_has_write_access"
                  @delete="removeGroupResourceProfile(item)"
                >
                  Are you sure you want to delete Group Resource Profile
                  <strong>{{ item.group_resource_profile_name }}</strong
                  >?
                </delete-link>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </main-layout>
</template>

<script>
import { Eye, Pencil, Plus } from "@lucide/vue";
import { components } from "django-airavata-common-ui";
import { services } from "django-airavata-api";

export default {
  name: "compute-resource-preference",
  components: {
    Eye,
    Pencil,
    Plus,
    "delete-link": components.DeleteLink,
    "human-date": components.HumanDate,
    "main-layout": components.MainLayout,
  },
  data: function () {
    return {
      groupResourceProfiles: [],
      fields: [
        {
          label: "Name",
          key: "group_resource_profile_name",
        },
        {
          label: "Updated",
          key: "updated_time",
        },
        {
          label: "Action",
          key: "action",
        },
      ],
    };
  },
  methods: {
    newGroupResourcePreference: function () {
      this.$router.push({
        name: "new_group_resource_preference",
      });
    },
    loadGroupResourceProfiles: function () {
      services.GroupResourceProfileService.list().then(
        (groupResourceProfiles) => {
          this.groupResourceProfiles = groupResourceProfiles;
        },
      );
    },
    removeGroupResourceProfile: function (groupResourceProfile) {
      services.GroupResourceProfileService.delete({
        lookup: groupResourceProfile.group_resource_profile_id,
      })
        .then(() => services.GroupResourceProfileService.list())
        .then(
          (groupResourceProfiles) =>
            (this.groupResourceProfiles = groupResourceProfiles),
        );
    },
  },
  mounted: function () {
    this.loadGroupResourceProfiles();
  },
};
</script>
