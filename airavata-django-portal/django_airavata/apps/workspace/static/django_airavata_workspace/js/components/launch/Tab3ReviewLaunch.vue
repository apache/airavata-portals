<template>
  <div>
    <div v-if="loading" class="text-muted">Generating preview…</div>
    <div v-else-if="error" class="alert alert-danger">
      <div>{{ error }}</div>
      <button class="btn btn-sm btn-outline-light mt-2" @click="refresh">Retry</button>
    </div>
    <div v-else-if="store.preview">
      <ul v-if="store.preview.warnings.length" class="alert alert-warning small" data-test="warnings">
        <li v-for="w in store.preview.warnings" :key="w">{{ w }}</li>
      </ul>
      <InvocationCommand :command="store.preview.invocation_command" />
      <ScriptPreview :script="store.preview.script_contents" />
      <div v-if="launchError" class="alert alert-danger mt-2">
        {{ launchError }}
        <button class="btn btn-sm btn-outline-light ms-2" @click="onLaunch">Try again</button>
      </div>
    </div>
    <div class="d-flex justify-content-end mt-3">
      <button
        class="btn btn-primary"
        data-test="launch"
        :disabled="!store.preview || loading"
        @click="onLaunch"
      >
        Launch experiment
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import { launcherService } from "django-airavata-common-ui/js/services/launcherService";
import InvocationCommand from "./InvocationCommand.vue";
import ScriptPreview from "./ScriptPreview.vue";

const store = useLaunchStore();
const loading = ref(false);
const error = ref<string | null>(null);
const launchError = ref<string | null>(null);
let abort: AbortController | null = null;

async function refresh() {
  if (store.preview && store.lastPreviewedHash === store.draftHash) return;
  loading.value = true;
  error.value = null;
  abort?.abort();
  abort = new AbortController();
  try {
    const r = await launcherService.generatePreview(store.draft, abort.signal);
    store.preview = r;
    store.lastPreviewedHash = store.draftHash;
  } catch (e) {
    error.value = (e as Error).message;
    store.preview = null;
  } finally {
    loading.value = false;
  }
}

async function onLaunch() {
  launchError.value = null;
  try {
    const { experiment_id } = await launcherService.launchExperiment(store.draft);
    window.location.href = `/workspace/experiments/${experiment_id}`;
  } catch (e) {
    launchError.value = (e as Error).message;
  }
}

onMounted(() => { void refresh(); });
</script>
