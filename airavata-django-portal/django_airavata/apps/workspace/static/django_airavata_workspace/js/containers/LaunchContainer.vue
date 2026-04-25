<template>
  <div class="container-fluid">
    <ExperimentMetaHeader :projects="projects" />
    <WizardTabs :active="active" @update:active="onChangeTab" />
    <div data-test="active-tab" :data-active="active" />
    <section v-if="active === 1" role="tabpanel">
      <Tab1ApplicationInputs />
    </section>
    <section v-if="active === 2" role="tabpanel">
      <Tab2Runtime />
    </section>
    <section v-if="active === 3" role="tabpanel">
      <Tab3ReviewLaunch />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { launcherService } from "django-airavata-common-ui/js/services/launcherService";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import ExperimentMetaHeader from "../components/launch/ExperimentMetaHeader.vue";
import WizardTabs from "../components/launch/WizardTabs.vue";
import Tab1ApplicationInputs from "../components/launch/Tab1ApplicationInputs.vue";
import Tab2Runtime from "../components/launch/Tab2Runtime.vue";
import Tab3ReviewLaunch from "../components/launch/Tab3ReviewLaunch.vue";

const active = ref<1 | 2 | 3>(1);
const projects = ref<Array<{ project_id: string; name: string }>>([]);
const store = useLaunchStore();

function onChangeTab(n: 1 | 2 | 3) {
  active.value = n;
  const url = new URL(window.location.href);
  url.searchParams.set("tab", String(n));
  window.history.replaceState({}, "", url);
}

onMounted(async () => {
  store.hydrate();
  const url = new URL(window.location.href);
  const t = Number(url.searchParams.get("tab"));
  if (t === 1 || t === 2 || t === 3) active.value = t as 1 | 2 | 3;
  const r = await launcherService.listProjects();
  projects.value = r?.results ?? [];
});
</script>
