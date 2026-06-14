<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">Groups</h1>
      <Button as="a" href="create">
        Create New Group
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </div>
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
  </div>
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
