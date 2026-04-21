<template>
  <list-layout
    :items="sortedModules"
    title="Application Catalog"
    subtitle="Applications"
    new-item-button-text="New Application"
    :new-button-disabled="false"
    @add-new-item="newApplicationHandler"
  >
    <template #item-list="slotProps">
      <div class="row">
        <application-card
          v-for="item in slotProps.items"
          :key="item.app_module_id"
          :app-module="item"
          @app-selected="clickHandler(item)"
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
  computed: {
    sortedModules() {
      if (this.appModules) {
        return utils.StringUtils.sortIgnoreCase(this.appModules.slice(), (a) => a.app_module_name);
      } else {
        return [];
      }
    },
    isGatewayAdmin() {
      return session.Session.is_gateway_admin;
    },
  },
  created() {
    this.loadApplications();
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
        (appModules) => (this.appModules = appModules),
      );
    },
  },
};
</script>
