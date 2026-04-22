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

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { layouts, components as comps } from "django-airavata-common-ui";
import { services, utils } from "django-airavata-api";

const ListLayout = layouts.ListLayout;
const ApplicationCard = comps.ApplicationCard;

const router = useRouter();
const appModules = ref<unknown[]>([]);

const sortedModules = computed(() => {
  if (appModules.value) {
    return utils.StringUtils.sortIgnoreCase(
      appModules.value.slice(),
      (a: { app_module_name: string }) => a.app_module_name,
    );
  } else {
    return [];
  }
});

onMounted(() => {
  services.ApplicationModuleService.listAll().then(
    (mods: unknown[]) => (appModules.value = mods),
  );
});

function clickHandler(item: { app_module_id: string }) {
  router.push({
    name: "application_module",
    params: { id: item.app_module_id },
  });
}

function newApplicationHandler() {
  router.push({ name: "new_application_module" });
}
</script>
