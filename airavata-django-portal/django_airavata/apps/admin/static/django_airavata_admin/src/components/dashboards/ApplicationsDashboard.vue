<template>
  <list-layout
    @add-new-item="newApplicationHandler"
    :items="sortedModules"
    title="Application Catalog"
    subtitle="Applications"
    new-item-button-text="New Application"
    :new-button-disabled="!isGatewayAdmin"
  >
    <template slot="item-list" slot-scope="slotProps">
      <div class="row">
        <application-card
          v-for="item in slotProps.items"
          v-bind:app-module="item"
          v-bind:key="item.app_module_id"
          v-on:app-selected="clickHandler(item)"
        >
        </application-card>
      </div>
    </template>
  </list-layout>
</template>
<script>
import { layouts, components as comps } from "django-airavata-common-ui";

import { services, session, utils } from "django-airavata-api";

export default {
  components: {
    "application-card": comps.ApplicationCard,
    "list-layout": layouts.ListLayout,
  },
  data() {
    return {
      appModules: [],
    };
  },
  created() {
    this.loadApplications();
  },
  computed: {
    sortedModules() {
      if (this.appModules) {
        return utils.StringUtils.sortIgnoreCase(
          this.appModules.slice(),
          (a) => a.app_module_name
        );
      } else {
        return [];
      }
    },
    isGatewayAdmin() {
      return session.Session.isGatewayAdmin;
    },
  },
  methods: {
    clickHandler(item) {
      this.$router.push({
        name: "application_module",
        params: { id: item.app_module_id },
      });
    },
    newApplicationHandler() {
      this.$router.push({ name: "new_application_module" });
    },
    loadApplications() {
      services.ApplicationModuleService.listAll().then(
        (appModules) => (this.appModules = appModules)
      );
    },
  },
};
</script>
