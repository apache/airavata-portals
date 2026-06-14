<template>
  <main-layout
    title="Application Catalog"
    subtitle="Browse and manage the applications available on this gateway."
  >
    <template v-slot:actions>
      <Button :disabled="!isGatewayAdmin" @click="newApplicationHandler">
        New Application
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </template>
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <application-card
        v-for="item in sortedModules"
        v-bind:app-module="item"
        v-bind:key="item.app_module_id"
        v-on:app-selected="clickHandler(item)"
      >
      </application-card>
    </div>
  </main-layout>
</template>
<script>
import { Plus } from "@lucide/vue";
import { components, components as comps } from "django-airavata-common-ui";

import { services, session, utils } from "django-airavata-api";

export default {
  components: {
    Plus,
    "application-card": comps.ApplicationCard,
    "main-layout": components.MainLayout,
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
          (a) => a.app_module_name,
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
        (appModules) => (this.appModules = appModules),
      );
    },
  },
};
</script>
