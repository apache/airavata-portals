<template>
  <div>
    <section class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Application</div>
      <AppPicker :applications="apps" />
    </section>
    <section v-if="store.pickedApp" class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Interface</div>
      <InterfacePicker />
    </section>
    <section v-if="store.pickedInterface" data-test="inputs-section" class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Inputs</div>
      <InputList :storages="store.storages" />
    </section>
    <section v-if="store.pickedInterface && fileOutputCount > 0" class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Outputs</div>
      <OutputList :storages="store.storages" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { launcherService } from "django-airavata-common-ui/js/services/launcherService";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import type { Application } from "django-airavata-common-ui/js/stores/launch-types";
import AppPicker from "./AppPicker.vue";
import InterfacePicker from "./InterfacePicker.vue";
import InputList from "./InputList.vue";
import OutputList from "./OutputList.vue";

const store = useLaunchStore();
const apps = ref<Application[]>([]);

onMounted(async () => {
  const [a, s] = await Promise.all([launcherService.listApplications(), launcherService.listUserStorages()]);
  apps.value = a?.results ?? [];
  store.setStorages(s?.results ?? []);
});

const fileOutputCount = computed(() =>
  (store.pickedInterface?.outputs ?? []).filter((o) => o.type === "file" || o.type === "dir").length,
);
</script>
