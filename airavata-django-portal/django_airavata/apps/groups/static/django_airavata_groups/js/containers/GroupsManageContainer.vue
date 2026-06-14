<template>
  <main-layout
    title="Groups"
    subtitle="Create and manage groups to share resources with other users."
  >
    <template #actions>
      <Button as="a" href="create">
        Create New Group
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </template>
    <Card>
      <CardContent>
        <group-list :groupsForOwners="groupsOwners"></group-list>
        <pager
          :paginator="groupPaginator"
          @next="nextGroups"
          @previous="previousGroups"
        ></pager>
      </CardContent>
    </Card>
  </main-layout>
</template>

<script>
import GroupList from "../group_components/GroupList.vue";
import { Plus } from "@lucide/vue";

import { services } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";

export default {
  name: "groups-manage-container",
  data() {
    return {
      groupPaginator: null,
    };
  },
  components: {
    "main-layout": comps.MainLayout,
    "group-list": GroupList,
    pager: comps.Pager,
    Plus,
  },
  methods: {
    nextGroups: function () {
      this.groupPaginator.next();
    },
    previousGroups: function () {
      this.groupPaginator.previous();
    },
  },
  computed: {
    groupsOwners: function () {
      return this.groupPaginator ? this.groupPaginator.results : null;
    },
  },
  beforeMount: function () {
    services.GroupService.list().then(
      (result) => (this.groupPaginator = result)
    );
  },
};
</script>
