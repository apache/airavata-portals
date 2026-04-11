<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Sharing</h1>
        <p class="text-muted mb-0">Create and manage groups to share resources with other users.</p>
      </div>
      <div class="col-auto">
        <a href="/resources/sharing/create" class="btn btn-primary btn-sm">
          <i class="fa fa-plus me-1"></i>Create New Group
        </a>
      </div>
    </div>
    <div class="card">
      <div class="card-body">
        <group-list v-bind:groupsForOwners="groupsOwners"></group-list>
        <pager
          v-if="groupsOwners && groupsOwners.length > 0"
          v-bind:paginator="groupPaginator"
          v-on:next="nextGroups"
          v-on:previous="previousGroups"
        ></pager>
      </div>
    </div>
  </div>
</template>

<script>
import GroupList from "../group_components/GroupList.vue";

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
